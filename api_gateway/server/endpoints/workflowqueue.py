import datetime
import json
import uuid
import logging
from collections import OrderedDict

from flask import request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_claims
from sqlalchemy import exists, and_, or_
import gevent

from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, StatementError

from common.message_types import StatusEnum, WorkflowStatusMessage
from api_gateway.events import WalkoffEvent
from api_gateway.executiondb.workflow import Workflow, WorkflowSchema
from api_gateway.executiondb.workflowresults import WorkflowStatus, WorkflowStatusSchema, WorkflowStatusSummarySchema
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, validate_resource_exists_factory, is_valid_uid, \
    paginate
from api_gateway.server.problem import Problem, dne_problem, invalid_input_problem, improper_json_problem
from api_gateway.server.endpoints.results import push_to_action_stream_queue, push_to_workflow_stream_queue
from http import HTTPStatus

logger = logging.getLogger(__name__)


def log_and_send_event(event, sender=None, data=None, workflow=None):
    sender = sender
    current_app.running_context.results_sender.handle_event(workflow, sender, event=event, data=data)


def abort_workflow(execution_id, user=None):
    """Abort a workflow
    Args:
        execution_id (UUID): The execution id of the workflow.
        user (str, Optional): The username of the user who requested that this workflow be aborted. Defaults
            to None.
    Returns:
        (bool): True if successfully aborted workflow, False otherwise
    """
    logger.info(f"User {user} aborting workflow {execution_id}")
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=execution_id).first()

    if workflow_status:
        if workflow_status.status in [StatusEnum.PENDING, StatusEnum.PAUSED,
                                      StatusEnum.AWAITING_DATA]:
            workflow = current_app.running_context.execution_db.session.query(Workflow).filter_by(
                id=workflow_status.workflow_id).first()
            if workflow is not None:
                data = {}
                if user:
                    data['user'] = user
                log_and_send_event(event=WalkoffEvent.WorkflowAborted,
                                   sender={'execution_id': execution_id, 'id': workflow_status.workflow_id,
                                           'name': workflow.name}, workflow=workflow, data=data)
        elif workflow_status.status == StatusEnum.EXECUTING:
            print("I guess Im here")
            # self.zmq_workflow_comm.abort_workflow(execution_id)
        return True
    else:
        logger.warning(f"Cannot resume workflow {execution_id}. Invalid key, or workflow already shutdown.")
    return False


def does_workflow_exist(workflow_id):
    return current_app.running_context.execution_db.session.query(exists().where(Workflow.id_ == workflow_id)).scalar()


def does_execution_id_exist(execution_id):
    return current_app.running_context.execution_db.session.query(
        exists().where(WorkflowStatus.execution_id == execution_id)).scalar()


def workflow_status_getter(execution_id):
    return current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=execution_id).first()


def workflow_getter(workflow_id):
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id_=workflow_id).first()


workflow_schema = WorkflowSchema()
workflow_status_schema = WorkflowStatusSchema()
workflow_status_summary_schema = WorkflowStatusSummarySchema()

with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)

with_workflow_status = with_resource_factory('workflow', workflow_status_getter, validator=is_valid_uid)
validate_workflow_is_registered = validate_resource_exists_factory('workflow', does_workflow_exist)
validate_execution_id_is_registered = validate_resource_exists_factory('workflow', does_execution_id_exist)

status_order = OrderedDict(
    [((StatusEnum.EXECUTING, StatusEnum.AWAITING_DATA, StatusEnum.PAUSED),
      WorkflowStatus.started_at),
     ((StatusEnum.ABORTED, StatusEnum.COMPLETED), WorkflowStatus.completed_at)])

executing_statuses = (StatusEnum.EXECUTING, StatusEnum.AWAITING_DATA, StatusEnum.PAUSED)
completed_statuses = (StatusEnum.ABORTED, StatusEnum.COMPLETED)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
@paginate(workflow_status_summary_schema)
def get_all_workflow_status():
    r = current_app.running_context.execution_db.session.query(WorkflowStatus).order_by(WorkflowStatus.name).all()
    return r, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
@with_workflow_status('control', 'execution_id')
def get_workflow_status(execution_id):
    workflow_status = workflow_status_schema.dump(execution_id)
    return workflow_status, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['execute']))
def execute_workflow():
    data = request.get_json()
    workflow_id = data.get("workflow_id")
    execution_id = data.get("execution_id", str(uuid.uuid4()))
    workflow = workflow_getter(workflow_id)  # ToDo: should this go under a path param so we can use the decorator

    if not workflow:
        return dne_problem("workflow", "execute", workflow_id)

    if not workflow.is_valid:
        return invalid_input_problem("workflow", "execute", workflow.id_, errors=workflow.errors)

    workflow = workflow_schema.dump(workflow)

    if "workflow_variables" in workflow and "workflow_variables" in data:
        # TODO: change these on the db model to be keyed by ID
        # Get workflow variables keyed by ID
        current_wvs = {wv['id_']: wv for wv in workflow["workflow_variables"]}
        new_wvs = {wv['id_']: wv for wv in data["workflow_variables"]}

        # Update workflow variables with new values, ignore ids that didn't already exist
        override_wvs = {id_: new_wvs[id_] if id_ in new_wvs else current_wvs[id_] for id_ in current_wvs}
        workflow["workflow_variables"] = list(override_wvs.values())

    try:
        workflow_status_json = {  # ToDo: Probably load this directly into db model?
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "name": workflow["name"],
            "status": StatusEnum.PENDING.name,
            "started_at": None,
            "completed_at": None,
            "user": get_jwt_claims().get('username', None),
            "action_statuses": []
        }
        workflow_status = workflow_status_schema.load(workflow_status_json)
        current_app.running_context.execution_db.session.add(workflow_status)
        current_app.running_context.execution_db.session.commit()

        workflow_message = {"workflow": workflow, "workflow_id": workflow_id, "execution_id": execution_id}
        # ToDo: self.__box.encrypt(message))
        current_app.running_context.cache.lpush("workflow-queue", json.dumps(workflow_message))

        gevent.spawn(push_to_workflow_stream_queue, workflow_status_json, "PENDING")
        current_app.logger.info(f"Created Workflow Status {workflow['name']} ({execution_id})")

        return jsonify({'execution_id': execution_id}), HTTPStatus.ACCEPTED
    except ValidationError as e:
        current_app.running_context.execution_db.session.rollback()
        return improper_json_problem('workflow_status', 'create', workflow['name'], e.messages)


# ToDo: Ensure workflow abort works
def control_workflow():
    data = request.get_json()
    execution_id = data['execution_id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('workflows', ['execute']))
    @validate_execution_id_is_registered('control', execution_id)
    def __func():
        status = data['status']

        if status == 'pause':
            current_app.running_context.executor.pause_workflow(execution_id,
                                                                user=get_jwt_claims().get('username', None))
        elif status == 'resume':
            current_app.running_context.executor.resume_workflow(execution_id,
                                                                 user=get_jwt_claims().get('username', None))
        elif status == 'abort':
            abort_workflow(execution_id, user=get_jwt_claims().get('username', None))

        return None, HTTPStatus.NO_CONTENT

    return __func()


# ToDo: make these clear db endpoints for more resources
def clear_workflow_status(all=False, days=30):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
    def __func():
        if all:
            current_app.running_context.execution_db.session.query(WorkflowStatus).filter(or_(
                WorkflowStatus.status == StatusEnum.ABORTED,
                WorkflowStatus.status == StatusEnum.COMPLETED
            )).delete()
        elif days > 0:
            delete_date = datetime.datetime.today() - datetime.timedelta(days=days)
            current_app.running_context.execution_db.session.query(WorkflowStatus).filter(and_(
                WorkflowStatus.status.in_([StatusEnum.ABORTED, StatusEnum.COMPLETED]),
                WorkflowStatus.completed_at <= delete_date
            )).delete(synchronize_session=False)
        current_app.running_context.execution_db.session.commit()
        return None, HTTPStatus.NO_CONTENT

    return __func()
