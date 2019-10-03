import uuid
import json
from uuid import UUID
import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
import jsonpatch
from starlette.websockets import WebSocket
from fastapi import APIRouter, Depends, HTTPException
from typing import Union

from api.server.utils.problems import UniquenessException
from api.server.db.workflowresults import WorkflowStatus, NodeStatus
from api.server.db import get_mongo_c
from common.redis_helpers import connect_to_aioredis_pool
from common.config import config

logger = logging.getLogger(__name__)
router = APIRouter()

WORKFLOW_STREAM_GLOB = "workflow_stream"
ACTION_STREAM_GLOB = "action_stream"


class JSONPatch(BaseModel):
    op: str
    path: str
    value: str
    start: str


async def workflow_status_getter(execution_id, workflow_col: AsyncIOMotorCollection):
    return await workflow_col.find_one({"execution_id": execution_id}, projection={"_id": False})


async def node_status_getter(combined_id, node_col: AsyncIOMotorCollection):
    return await node_col.find_one({"combined_id": combined_id}, projection={"_id": False})


# results_stream = Blueprint('results_stream', __name__)
workflow_stream_subs = set()
action_stream_subs = set()


async def push_to_workflow_stream_queue(workflow_status: WorkflowStatus, event):
    if workflow_status.node_status is not None:
        workflow_status.node_status = []
    # workflow_status.pop("node_statuses", None)
    workflow_status.execution_id = str(workflow_status.execution_id)
    redis_stream = None
    # sse_event_text = sse_format(data=workflow_status, event=event, event_id=workflow_status["execution_id"])
    if workflow_status.execution_id in workflow_stream_subs:
        redis_stream = WORKFLOW_STREAM_GLOB + "." + workflow_status.execution_id
        # workflow_stream_subs[workflow_status["execution_id"]].put(sse_event_text)
    if 'all' in workflow_stream_subs:
        redis_stream = WORKFLOW_STREAM_GLOB + ".all"

    if redis_stream is not None:
        async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
            key = f"{redis_stream}"
            value = workflow_status.json()
            # print(type(value))
            await conn.lpush(key, value)


async def push_to_action_stream_queue(node_statuses: NodeStatus, event):

    for node_status in node_statuses:
        node_status_json = node_status
        node_status_json["execution_id"] = str(node_status_json["execution_id"])
        execution_id = str(node_status_json["execution_id"])
        # sse_event_text = sse_format(data=node_status_json, event=event, event_id=event_id)

        if execution_id in action_stream_subs:
            redis_stream = ACTION_STREAM_GLOB + "." + node_status_json["execution_id"]
            # action_stream_subs[execution_id].put(sse_event_text)
        elif 'all' in action_stream_subs:
            redis_stream = ACTION_STREAM_GLOB + ".all"
            # action_stream_subs['all'].put(sse_event_text)
        else:
            redis_stream = WORKFLOW_STREAM_GLOB + "." + node_status_json["execution_id"]
            action_stream_subs.add(node_status_json["execution_id"])
            redis_stream = ACTION_STREAM_GLOB + "." + node_status_json["execution_id"]

        async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
            key = f"{redis_stream}"
            value = node_status_json
            await conn.lpush(key, value)


# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions("workflowstatus", ["create"]))
# def create_workflow_status():
#     workflow_status_json = request.get_json()
#     workflow_id = workflow_status_json.get("workflow_id")
#     workflow = workflow_getter(workflow_id)
#     current_app.logger.info(workflow_id)
#     # if not workflow.is_valid:
#     #     return invalid_input_problem("workflow", "execute", workflow.id_, errors=workflow.errors)
#
#     execution_id = str(uuid.uuid4())
#
#     workflow_status_json["status"] = "PENDING"
#     workflow_status_json["name"] = workflow.name
#     workflow_status_json["execution_id"] = execution_id
#
#     try:
#         workflow_status = workflow_status_schema.load(workflow_status_json)
#         current_app.running_context.execution_db.session.add(workflow_status)
#         current_app.running_context.execution_db.session.commit()
#         gevent.spawn(push_to_workflow_stream_queue, workflow_status_json, "PENDING")
#         current_app.logger.info(f"Created Workflow Status {workflow.name} ({execution_id})")
#         return jsonify({'id': execution_id}), HTTPStatus.ACCEPTED
#     except ValidationError as e:
#         current_app.running_context.execution_db.session.rollback()
#         return improper_json_problem('workflow_status', 'create', workflow.name, e.messages)
#     except IntegrityError:
#         current_app.running_context.execution_db.session.rollback()
#         return unique_constraint_problem('workflow_status', 'create', workflow.name)

# TODO: maybe make an internal user for the worker/umpire?
@router.put("/workflow_status/{execution_id}")
async def update_workflow_status(body: JSONPatch, event: str, execution_id: str,
                                 workflow_col: AsyncIOMotorCollection = Depends((get_mongo_c)), close: str = None):
    old_workflow = workflow_status_getter(execution_id, workflow_col)
    old_workflow_status = old_workflow.status

    # TODO: change these on the db model to be keyed by ID
    if "node_statuses" in old_workflow_status:
        old_workflow_status.node_statuses = {astat['node_id']: astat for astat in old_workflow_status.node_statuses}
    else:
        old_workflow_status.node_statuses = {}

    patch = jsonpatch.JsonPatch.from_string(json.dumps(body))

    logger.debug(f"Patch: {patch}")
    logger.debug(f"Old Workflow Status: {old_workflow_status}")

    new_workflow_status = patch.apply(old_workflow_status)

    new_workflow_status.node_statuses = list(new_workflow_status.node_statuses.values())
    if close is not None and close == "Done":
        new_workflow_status.websocket_finished = True
    else:
        new_workflow_status.websocket_finished = False

    try:
        await workflow_col.replace_one(old_workflow, new_workflow_status)
        # execution_id = workflow_status_schema.load(new_workflow_status, instance=execution_id)
        # current_app.running_context.execution_db.session.commit()

        node_statuses = []
        for patch in body:
            if "node_statuses" in patch["path"]:
                node_statuses.append(node_status_getter(patch["value"]["combined_id"]))

        # TODo: Replace this when moving to sanic
        logger.info(f"Workflow Status update: {new_workflow_status}")
        await push_to_workflow_stream_queue(new_workflow_status, event)
        # gevent.spawn(push_to_workflow_stream_queue, new_workflow_status, event)

        if node_statuses:
            logger.info(f"Action Status update:{node_statuses}")
            await push_to_action_stream_queue(node_statuses, event)
            # gevent.spawn(push_to_action_stream_queue, node_statuses, event)

        logger.info(f"Updated workflow status {old_workflow.execution_id} ({old_workflow.name})")
        return new_workflow_status
    except Exception as e:
        return UniquenessException('workflow status', 'update', old_workflow.id_)


@router.websocket_route('/workflow_status/')
async def workflow_stream(websocket: WebSocket, exec_id: Union[UUID, str] = "all"):
    await websocket.accept()
    redis_stream = WORKFLOW_STREAM_GLOB + "." + str(exec_id)
    if exec_id not in workflow_stream_subs:
        workflow_stream_subs.add(exec_id)
    logger.info(f"workflow_status subscription for {exec_id}")
    # if exec_id != 'all':
    #     try:
    #         uuid.UUID(exec_id)
    #     except ValueError:
    #         return invalid_id_problem('workflow status', 'read', exec_id)

    async def workflow_results_generator():
        async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
            try:
                while True:
                    await asyncio.sleep(1)
                    event = conn.rpop(redis_stream)
                    if event is not None:
                        event_object = json.loads(event.decode("ascii"))
                        message = event_object["message"]
                        await websocket.send_text(message)
                        logger.info(f"Sending workflow_status SSE for {exec_id}: {event}")
                        if event_object["close"] == "Done":
                            await conn.delete(redis_stream)
                            workflow_stream_subs.remove(exec_id)
                            await websocket.close(code=1000)
            except Exception as e:
                await conn.delete(redis_stream)
                workflow_stream_subs.remove(exec_id)
                await websocket.close(code=1000)
                logger.info(f"Error: {e}")

    return await workflow_results_generator()
        # Response(workflow_results_generator(), mimetype="test/event-stream")


@router.websocket_route('/actions/')
async def action_stream(websocket: WebSocket, exec_id: Union[UUID, str] = "all"):
    await websocket.accept()
    redis_stream = ACTION_STREAM_GLOB + "." + str(exec_id)
    if exec_id not in action_stream_subs:
        action_stream_subs.add(exec_id)
    logger.info(f"action subscription for {exec_id}")
    # if execution_id != 'all':
    #     try:
    #         uuid.UUID(execution_id)
    #     except ValueError:
    #         return invalid_id_problem('action status', 'read', execution_id)

    async def action_results_generator():
        async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
            try:
                while True:
                    await asyncio.sleep(1)
                    event = conn.rpop(redis_stream)
                    if event is not None:
                        event_object = json.loads(event.decode("ascii"))
                        message = event_object["message"]
                        await websocket.send_text(message)
                        logger.info(f"Sending action websocket for for {exec_id}: {message}")
                        if event_object["close"] == "Done":
                            await conn.delete(redis_stream)
                            action_stream_subs.remove(exec_id)
                            await websocket.close(code=1000)
            except Exception as e:
                await conn.delete(redis_stream)
                action_stream_subs.remove(exec_id)
                await websocket.close(code=1000)
                logger.info(f"Error: {e}")

    return await action_results_generator()
