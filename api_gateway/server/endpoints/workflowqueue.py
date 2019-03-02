import datetime
import json
import uuid
import logging
from collections import OrderedDict

from flask import request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_claims
from sqlalchemy import exists, and_, or_

from api_gateway.events import WalkoffEvent
from api_gateway.executiondb.workflow import Workflow
from api_gateway.executiondb.workflowresults import WorkflowStatus, WorkflowStatusEnum
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, validate_resource_exists_factory, is_valid_uid
from api_gateway.server.problem import Problem
from api_gateway.server.returncodes import *
from api_gateway.executiondb.schemas import WorkflowSchema


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
    logger.info('User {0} aborting workflow {1}'.format(user, execution_id))
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(execution_id=execution_id).first()

    if workflow_status:
        if workflow_status.status in [WorkflowStatusEnum.pending, WorkflowStatusEnum.paused,
                                      WorkflowStatusEnum.awaiting_data]:
            workflow = current_app.running_context.execution_db.session.query(Workflow).filter_by(id=workflow_status.workflow_id).first()
            if workflow is not None:
                data = {}
                if user:
                    data['user'] = user
                log_and_send_event(event=WalkoffEvent.WorkflowAborted,
                                   sender={'execution_id': execution_id, 'id': workflow_status.workflow_id,
                                           'name': workflow.name}, workflow=workflow, data=data)
        elif workflow_status.status == WorkflowStatusEnum.running:
            print("I guess Im here")
            # self.zmq_workflow_comm.abort_workflow(execution_id)
        return True
    else:
        logger.warning(
            'Cannot resume workflow {0}. Invalid key, or workflow already shutdown.'.format(execution_id))
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
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()


with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)

with_workflow_status = with_resource_factory('workflow', workflow_status_getter, validator=is_valid_uid)
validate_workflow_is_registered = validate_resource_exists_factory('workflow', does_workflow_exist)
validate_execution_id_is_registered = validate_resource_exists_factory('workflow', does_execution_id_exist)

status_order = OrderedDict(
    [((WorkflowStatusEnum.running, WorkflowStatusEnum.awaiting_data, WorkflowStatusEnum.paused),
      WorkflowStatus.started_at),
     ((WorkflowStatusEnum.aborted, WorkflowStatusEnum.completed), WorkflowStatus.completed_at)])

executing_statuses = (WorkflowStatusEnum.running, WorkflowStatusEnum.awaiting_data, WorkflowStatusEnum.paused)
completed_statuses = (WorkflowStatusEnum.aborted, WorkflowStatusEnum.completed)


def get_all_workflow_status():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        page = request.args.get('page', 1, type=int)

        ret = current_app.running_context.execution_db.session.query(WorkflowStatus). \
            order_by(WorkflowStatus.status, WorkflowStatus.started_at.desc()). \
            limit(current_app.config['ITEMS_PER_PAGE']). \
            offset((page - 1) * current_app.config['ITEMS_PER_PAGE'])

        ret = jsonify([workflow_status.as_json() for workflow_status in ret])
        return ret, SUCCESS

    return __func()


def get_workflow_status(execution_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    @with_workflow_status('control', execution_id)
    def __func(workflow_status):
        return workflow_status.as_json(full_actions=True), SUCCESS

    return __func()


def execute_workflow():
    data = request.get_json()
    workflow_id = data['workflow_id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @with_workflow('execute', workflow_id)
    def __func(workflow):
        if not workflow.is_valid:
            return Problem(INVALID_INPUT_ERROR, 'Cannot execute workflow', 'Workflow is invalid')

        # Short circuits the multiprocessed executor
        workflow = current_app.running_context.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()
        workflow_schema = WorkflowSchema()
        workflow = workflow_schema.dump(workflow)
        execution_id = str(uuid.uuid4())

        workflow_data = {'execution_id': execution_id, 'id': workflow["id"], 'name': workflow["name"]}
        current_app.running_context.results_sender.handle_event(workflow=workflow, sender=workflow_data,
                                    event=WalkoffEvent.WorkflowExecutionPending, data=data)

        message = {"workflow": workflow, "workflow_id": str(workflow_id), "execution_id": execution_id}
        current_app.running_context.cache.lpush("workflow-queue", json.dumps(message))  # self.__box.encrypt(message))

        current_app.running_context.results_sender.handle_event(workflow=workflow, sender=workflow_data,
                                    event=WalkoffEvent.SchedulerJobExecuted, data=data)

        current_app.logger.info('Executed workflow {0}'.format(workflow_id))
        return {'id': execution_id}, SUCCESS_ASYNC

    return __func()


def control_workflow():
    data = request.get_json()
    execution_id = data['execution_id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
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

        return None, NO_CONTENT

    return __func()


def clear_workflow_status(all=False, days=30):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        if all:
            current_app.running_context.execution_db.session.query(WorkflowStatus).filter(or_(
                WorkflowStatus.status == WorkflowStatusEnum.aborted,
                WorkflowStatus.status == WorkflowStatusEnum.completed
            )).delete()
        elif days > 0:
            delete_date = datetime.datetime.today() - datetime.timedelta(days=days)
            current_app.running_context.execution_db.session.query(WorkflowStatus).filter(and_(
                WorkflowStatus.status.in_([WorkflowStatusEnum.aborted, WorkflowStatusEnum.completed]),
                WorkflowStatus.completed_at <= delete_date
            )).delete(synchronize_session=False)
        current_app.running_context.execution_db.session.commit()
        return None, NO_CONTENT

    return __func()
