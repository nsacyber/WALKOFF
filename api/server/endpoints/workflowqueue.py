import datetime
import json
import uuid
from http import HTTPStatus
import logging
from collections import OrderedDict
from datetime import datetime


import gevent
from starlette.requests import Request

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.db.permissions import auth_check
from common.config import config, static
from common.message_types import StatusEnum, message_dumps
from api.server.db import get_db, get_mongo_d, get_mongo_c
from api.server.db.workflowresults import WorkflowStatus, ExecuteWorkflow, ControlWorkflow
from api.security import get_jwt_claims, get_jwt_identity
from api.server.endpoints.results import push_to_workflow_stream_queue
from api.server.utils.problems import InvalidInputException, ImproperJSONException, DoesNotExistException

router = APIRouter()
logger = logging.getLogger(__name__)


def workflow_status_getter(execution_id, app_api_col: AsyncIOMotorCollection):
    return await app_api_col.find_one({"execution_id": execution_id}, projection={'_id': False})


def workflow_getter(workflow_id, app_api_col: AsyncIOMotorCollection):
    return await app_api_col.find_one({"workflow_id": workflow_id}, projection={'_id': False})


status_order = OrderedDict(
    [((StatusEnum.EXECUTING, StatusEnum.AWAITING_DATA, StatusEnum.PAUSED),
      WorkflowStatus.started_at),
     ((StatusEnum.ABORTED, StatusEnum.COMPLETED), WorkflowStatus.completed_at)])

executing_statuses = (StatusEnum.EXECUTING, StatusEnum.AWAITING_DATA, StatusEnum.PAUSED)
completed_statuses = (StatusEnum.ABORTED, StatusEnum.COMPLETED)


@router.get("/")
def get_all_workflow_status(request: Request, workflow_status_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    temp = []
    ret = []
    for wf_status in (await workflow_status_col.find().to_list(None)):
        temp.append(WorkflowStatus(**wf_status))

    for wf_status in temp:
        to_read = auth_check(curr_user_id, str(wf_status.workflow_id), "read", "workflows", walkoff_db=walkoff_db)
        if to_read:
            ret.append(wf_status)

    return ret, HTTPStatus.OK


@router.post("/")
def execute_workflow(workflow_to_execute: ExecuteWorkflow, request: Request, workflow_status_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)

    workflow_id = workflow_to_execute.workflow_id
    execution_id = workflow_to_execute.execution_id
    workflow = workflow_getter(workflow_id, workflow_status_col)
    data = dict(workflow_to_execute)

    curr_user_id = await get_jwt_identity(request)

    to_execute = auth_check(curr_user_id, str(workflow.id_), "execute", "workflows", walkoff_db=walkoff_db)
    if to_execute:
        if not workflow:
            return DoesNotExistException("workflow", "execute", workflow_id)

        if not workflow.is_valid:
            return InvalidInputException("workflow", "execute", workflow.id_, errors=workflow.errors)

        workflow = dict(workflow)

        actions_by_id = {a['id_']: a for a in workflow["actions"]}
        triggers_by_id = {t['id_']: t for t in workflow["triggers"]}

        # TODO: Add validation to all overrides
        if "start" in data:
            if data["start"] in actions_by_id or data["start"] in triggers_by_id:
                workflow["start"] = data["start"]
            else:
                raise InvalidInputException("execute", "workflow", workflow["id_"],
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
                raise InvalidInputException("workflow", "execute", workflow["id_"],
                                             errors=["Cannot override starting parameters for anything but an action."])

        try:
            execution_id = execute_workflow_helper(request=request, workflow_id=workflow_id, execution_id=execution_id,
                                                   workflow=workflow, workflow_status_col=workflow_status_col)
            return ({'execution_id': execution_id}), HTTPStatus.ACCEPTED
        except ValidationError as e:
            raise ImproperJSONException('workflow_status', 'create', workflow['name'], e.messages)
    else:
        return None, HTTPStatus.FORBIDDEN


def execute_workflow_helper(request: Request, workflow_id, workflow_status_col: AsyncIOMotorCollection, execution_id=None, workflow=None):
    if not execution_id:
        execution_id = str(uuid.uuid4())
    if not workflow:
        workflow = dict(workflow_getter(workflow_id, workflow_status_col))
    workflow_status_json = {  # ToDo: Probably load this directly into db model?
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "name": workflow["name"],
        "status": StatusEnum.PENDING.name,
        "started_at": str(datetime.now().isoformat()),
        "completed_at": None,
        "user": (await get_jwt_claims(request)).get('username', None),
        "node_statuses": [],
        "app_name": None,
        "action_name": None,
        "label": None
    }
    workflow_status = WorkflowStatus(**workflow_status_json)
    await workflow_status_col.insert_one(workflow_status_json)

    # Assign the execution id to the workflow so the worker knows it
    workflow["execution_id"] = execution_id
    # ToDo: self.__box.encrypt(message))
    current_app.running_context.cache.sadd(static.REDIS_PENDING_WORKFLOWS, execution_id)
    current_app.running_context.cache.xadd(static.REDIS_WORKFLOW_QUEUE,
                                           {execution_id: json.dumps(workflow)})
    gevent.spawn(push_to_workflow_stream_queue, workflow_status_json, "PENDING")
    logger.info(f"Created Workflow Status {workflow['name']} ({execution_id})")

    return execution_id


@router.get("/{execution}")
def get_workflow_status(request: Request, execution, workflow_status_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)
    workflow_status = dict(workflow_status_getter(execution, workflow_status_col))

    to_read = auth_check(curr_user_id, str(workflow_status['workflow_id']), "read", "workflows", walkoff_db=walkoff_db)
    if to_read:
        return workflow_status, HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@router.patch("/{execution}")
def control_workflow(request: Request, execution, workflow_to_control: ControlWorkflow, workflow_status_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    data = dict(workflow_to_control)
    status = data['status']

    workflow = workflow_getter(execution.workflow_id, workflow_status_col)
    # The resource factory returns the WorkflowStatus model but we want the string of the execution ID
    execution_id = str(execution.execution_id)

    to_execute = auth_check(curr_user_id, str(workflow.id_), "execute", "workflows", walkoff_db=walkoff_db)
    # TODO: add in pause/resume here. Workers need to store and recover state for this
    if to_execute:
        if status == 'abort':
            logger.info(f"User '{(await get_jwt_claims(request)).get('username', None)}' aborting workflow: {execution_id}")
            message = {"execution_id": execution_id, "status": status, "workflow": dict(workflow)}
            current_app.running_context.cache.smove(static.REDIS_PENDING_WORKFLOWS,
                                                    static.REDIS_ABORTING_WORKFLOWS, execution_id)
            current_app.running_context.cache.xadd(static.REDIS_WORKFLOW_CONTROL, message)

            return None, HTTPStatus.NO_CONTENT
        elif status == 'trigger':
            if execution.status not in (StatusEnum.PENDING, StatusEnum.EXECUTING, StatusEnum.AWAITING_DATA):
                raise InvalidInputException("workflow", "trigger", execution_id,
                                             errors=["Workflow must be in a running state to accept triggers."])

            trigger_id = data.get('trigger_id')
            if not trigger_id:
                raise InvalidInputException("workflow", "trigger", execution_id,
                                             errors=["ID of the trigger must be specified in trigger_id."])
            seen = False
            for trigger in workflow.triggers:
                if str(trigger.id_) == trigger_id:
                    seen = True

            if not seen:
                raise InvalidInputException("workflow", "trigger", execution_id,
                                             errors=[f"trigger_id {trigger_id} was not found in this workflow."])

            trigger_stream = f"{execution_id}-{trigger_id}:triggers"

            try:
                info = current_app.running_context.cache.xinfo_stream(trigger_stream)
                stream_length = info["length"]
            except Exception:
                stream_length = 0

            if stream_length > 0:
                return InvalidInputException("workflow", "trigger", execution_id,
                                             errors=[f"This trigger has already received data."])

            trigger_data = data.get('trigger_data')
            logger.info(f"User '{(await get_jwt_claims(request)).get('username', None)}' triggering workflow: {execution_id} at trigger "
                        f"{trigger_id} with data {trigger_data}")

            current_app.running_context.cache.xadd(trigger_stream,
                                                   {execution_id: message_dumps({"trigger_data": trigger_data})})

            return ({"trigger_stream": trigger_stream}), HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@router.delete("/cleardb")
# ToDo: make these clear db endpoints for more resources
def clear_workflow_status(all_=False, days=30, workflow_status_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    if all_:
        await workflow_status_col.remove({ "$or":
                                               [{"status": StatusEnum.ABORTED}, {"status": StatusEnum.COMPLETED}]},
                                                projection={'_id': False})
    elif days > 0:
        delete_date = datetime.datetime.today() - datetime.timedelta(days=days)

        temp = await workflow_status_col.find({ "$or":
                                               [{"status": StatusEnum.ABORTED}, {"status": StatusEnum.COMPLETED}]},
                                                projection={'_id': False})
        temp2 = await workflow_status_col.find({"completed_at": {"$lte": delete_date}},
                                              projection={'_id': False})

        to_delete = list((set(temp)).intersection(set(temp2)))
        await workflow_status_col.deleteMany(to_delete)
    return None, HTTPStatus.NO_CONTENT
