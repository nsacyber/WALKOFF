import datetime
import json
import uuid
import logging
from collections import OrderedDict
from datetime import datetime


from flask import request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_claims
from sqlalchemy import exists, and_, or_
import gevent

from marshmallow import ValidationError

from common.message_types import StatusEnum, message_dumps
from api_gateway.executiondb.workflow import Workflow, WorkflowSchema
from api_gateway.executiondb.workflowresults import WorkflowStatus, WorkflowStatusSchema
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, validate_resource_exists_factory, is_valid_uid, \
    paginate
from api_gateway.server.problem import dne_problem, invalid_input_problem, improper_json_problem
from api_gateway.server.endpoints.results import push_to_workflow_stream_queue
from http import HTTPStatus
from api_gateway.config import Config

logger = logging.getLogger(__name__)


def workflow_status_getter(execution_id):
    return current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=execution_id).first()


def workflow_getter(workflow_id):
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id_=workflow_id).first()


workflow_schema = WorkflowSchema()
workflow_status_schema = WorkflowStatusSchema()

with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)
with_workflow_status = with_resource_factory('workflow', workflow_status_getter, validator=is_valid_uid)


status_order = OrderedDict(
    [((StatusEnum.EXECUTING, StatusEnum.AWAITING_DATA, StatusEnum.PAUSED),
      WorkflowStatus.started_at),
     ((StatusEnum.ABORTED, StatusEnum.COMPLETED), WorkflowStatus.completed_at)])

executing_statuses = (StatusEnum.EXECUTING, StatusEnum.AWAITING_DATA, StatusEnum.PAUSED)
completed_statuses = (StatusEnum.ABORTED, StatusEnum.COMPLETED)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
@paginate(workflow_status_schema)  # ToDo: make this summary
def get_all_workflow_status():
    r = current_app.running_context.execution_db.session.query(WorkflowStatus).order_by(WorkflowStatus.name).all()
    return r, HTTPStatus.OK

@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
@with_workflow_status('control', 'execution')
def get_workflow_status(execution):
    workflow_status = workflow_status_schema.dump(execution)
    return workflow_status, HTTPStatus.OK

@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['execute']))
def execute_workflow():
    data = request.get_json()
    workflow_id = data.get("workflow_id")
    execution_id = data.get("execution_id", None)
    workflow = workflow_getter(workflow_id)  # ToDo: should this go under a path param so we can use the decorator

    if not workflow:
        return dne_problem("workflow", "execute", workflow_id)

    if not workflow.is_valid:
        return invalid_input_problem("workflow", "execute", workflow.id_, errors=workflow.errors)

    workflow = workflow_schema.dump(workflow)

    actions_by_id = {a['id_']: a for a in workflow["actions"]}
    triggers_by_id = {t['id_']: t for t in workflow["triggers"]}

    # TODO: Add validation to all overrides
    if "start" in data:
        if data["start"] in actions_by_id or data["start"] in triggers_by_id:
            workflow["start"] = data["start"]
        else:
            return invalid_input_problem("workflow", "execute", workflow.id_,
                                         errors=["Start override must be an action or a trigger in this workflow."])

    if "workflow_variables" in workflow and "workflow_variables" in data:
        # TODO: change these on the db model to be keyed by ID
        # Get workflow variables keyed by ID

        current_wvs = {wv['id_']: wv for wv in workflow["workflow_variables"]}
        new_wvs = {wv['id_']: wv for wv in data["workflow_variables"]}

        # Update workflow variables with new values, ignore ids that didn't already exist
        override_wvs = {id_: new_wvs[id_] if id_ in new_wvs else current_wvs[id_] for id_ in current_wvs}
        workflow["workflow_variables"] = list(override_wvs.values())

    if "parameters" in data:
        start_id = data.get("start", workflow["start"])
        if start_id in actions_by_id:
            parameters_by_name = {p["name"]: p for p in actions_by_id[start_id]["parameters"]}
            for parameter in data["parameters"]:
                parameters_by_name[parameter["name"]] = parameter
            actions_by_id[start_id]["parameters"] = list(parameters_by_name.values())
            workflow["actions"] = list(actions_by_id.values())
        else:
            return invalid_input_problem("workflow", "execute", workflow.id_,
                                         errors=["Cannot override starting parameters for anything but an action."])

    try:
        execution_id = execute_workflow_helper(workflow_id, execution_id, workflow)
        return jsonify({'execution_id': execution_id}), HTTPStatus.ACCEPTED
    except ValidationError as e:
        current_app.running_context.execution_db.session.rollback()
        return improper_json_problem('workflow_status', 'create', workflow['name'], e.messages)


def execute_workflow_helper(workflow_id, execution_id=None, workflow=None):
    if not execution_id:
        execution_id = str(uuid.uuid4())
    if not workflow:
        workflow = workflow_schema.dump(workflow_getter(workflow_id))
    workflow_status_json = {  # ToDo: Probably load this directly into db model?
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "name": workflow["name"],
        "status": StatusEnum.PENDING.name,
        "started_at": str(datetime.now().isoformat()),
        "completed_at": None,
        "user": get_jwt_claims().get('username', None),
        "node_statuses": []
    }
    workflow_status = workflow_status_schema.load(workflow_status_json)
    current_app.running_context.execution_db.session.add(workflow_status)
    current_app.running_context.execution_db.session.commit()

    # Assign the execution id to the workflow so the worker knows it
    workflow["execution_id"] = execution_id
    # ToDo: self.__box.encrypt(message))
    current_app.running_context.cache.sadd(Config.common_config.REDIS_PENDING_WORKFLOWS, execution_id)
    current_app.running_context.cache.xadd(Config.common_config.REDIS_WORKFLOW_QUEUE,
                                           {execution_id: json.dumps(workflow)})
    gevent.spawn(push_to_workflow_stream_queue, workflow_status_json, "PENDING")
    current_app.logger.info(f"Created Workflow Status {workflow['name']} ({execution_id})")

    return execution_id


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['execute']))
@with_workflow_status('control', "execution")
def control_workflow(execution):
    data = request.get_json()
    status = data['status']

    workflow = workflow_getter(execution.workflow_id)
    # The resource factory returns the WorkflowStatus model but we want the string of the execution ID
    execution_id = str(execution.execution_id)

    # TODO: add in pause/resume here. Workers need to store and recover state for this
    if status == 'abort':
        logger.info(f"User '{get_jwt_claims().get('username', None)}' aborting workflow: {execution_id}")
        message = {"execution_id": execution_id, "status": status, "workflow": workflow_schema.dumps(workflow)}
        current_app.running_context.cache.smove(Config.common_config.REDIS_PENDING_WORKFLOWS,
                                                Config.common_config.REDIS_ABORTING_WORKFLOWS, execution_id)
        current_app.running_context.cache.xadd(Config.common_config.REDIS_WORKFLOW_CONTROL, message)

        return None, HTTPStatus.NO_CONTENT
    elif status == 'trigger':
        if execution.status not in (StatusEnum.PENDING, StatusEnum.EXECUTING, StatusEnum.AWAITING_DATA):
            return invalid_input_problem("workflow", "trigger", execution_id,
                                         errors=["Workflow must be in a running state to accept triggers."])

        trigger_id = data.get('trigger_id')
        if not trigger_id:
            return invalid_input_problem("workflow", "trigger", execution_id,
                                         errors=["ID of the trigger must be specified in trigger_id."])
        seen = False
        for trigger in workflow.triggers:
            if str(trigger.id_) == trigger_id:
                seen = True

        if not seen:
            return invalid_input_problem("workflow", "trigger", execution_id,
                                         errors=[f"trigger_id {trigger_id} was not found in this workflow."])

        trigger_stream = f"{execution_id}-{trigger_id}:triggers"

        try:
            info = current_app.running_context.cache.xinfo_stream(trigger_stream)
            stream_length = info["length"]
        except Exception:
            stream_length = 0

        if stream_length > 0:
            return invalid_input_problem("workflow", "trigger", execution_id,
                                         errors=[f"This trigger has already received data."])

        trigger_data = data.get('trigger_data')
        logger.info(f"User '{get_jwt_claims().get('username', None)}' triggering workflow: {execution_id} at trigger "
                    f"{trigger_id} with data {trigger_data}")

        current_app.running_context.cache.xadd(trigger_stream,
                                               {execution_id: message_dumps({"trigger_data": trigger_data})})

        return jsonify({"trigger_stream": trigger_stream}), HTTPStatus.OK

# ToDo: make these clear db endpoints for more resources
def clear_workflow_status(all_=False, days=30):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
    def __func():
        if all_:
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
