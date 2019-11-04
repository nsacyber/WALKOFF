import uuid
import json
from uuid import UUID
import asyncio
import logging
import re
import traceback

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
import jsonpatch

from starlette.websockets import WebSocket
from fastapi import APIRouter, Depends, HTTPException
from typing import Union

from api.server.db import mongo
from api.server.utils.socketio import sio
from api.server.db.workflowresults import WorkflowStatus, NodeStatus, UpdateMessage
from api.server.db import get_mongo_c
from common.redis_helpers import connect_to_aioredis_pool
from common.config import config, static
from common.mongo_helpers import get_item, update_item

logger = logging.getLogger(__name__)
router = APIRouter()

WORKFLOW_STREAM_GLOB = "workflow_stream"
ACTION_STREAM_GLOB = "action_stream"


async def update_workflow_status():
    async with connect_to_aioredis_pool(config.REDIS_URI) as redis:
        wfq_col = mongo.async_client.walkoff_db.workflowqueue
        node_id_regex = r"/node_statuses/([0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12})"
        while True:
            try:
                logger.debug("Waiting for results...")
                message = (await redis.brpop(static.REDIS_RESULTS_QUEUE))[1]
                message = UpdateMessage(**json.loads(message.decode()))
                logger.debug(f"Got patches: {message.message}")

                old_workflow_status = await get_item(wfq_col, WorkflowStatus, message.execution_id,
                                                     id_key="execution_id")
                patch = jsonpatch.JsonPatch.from_string(message.message)
                new_workflow_status = WorkflowStatus(**patch.apply(old_workflow_status.dict()))

                update_wfs = await update_item(wfq_col, WorkflowStatus, message.execution_id, new_workflow_status,
                                               id_key="execution_id")

                if message.type == "workflow":
                    await sio.emit(static.SIO_EVENT_LOG, json.loads(update_wfs.json()),
                                   namespace=static.SIO_NS_WORKFLOW)
                else:
                    for patch in json.loads(message.message):
                        node_id = re.search(node_id_regex, patch["path"], re.IGNORECASE).group(1)
                        await sio.emit(static.SIO_EVENT_LOG, json.loads(update_wfs.node_statuses[node_id].json()),
                                       namespace=static.SIO_NS_NODE)
            except Exception as e:
                traceback.print_exc()

# # @sio.on(static.SIO_EVENT_LOG, namespace=static.SIO_NS_NODE)
# async def update_node_status():
#     # message = SIOMessage(**data)
#     logger.info(f"Got a log event: {message}")
#     wfq_col = mongo.async_client.walkoff_db.workflowqueue
#     old_workflow_status = await get_item(wfq_col, WorkflowStatus, message.execution_id, id_key="execution_id")
#
#     patch = jsonpatch.JsonPatch.from_string(message.message)
#     new_workflow_status = WorkflowStatus(**patch.apply(old_workflow_status.dict()))
#
#     r = await update_item(wfq_col, WorkflowStatus, message.execution_id, new_workflow_status, id_key="execution_id")
#     print(r)
#
#
# async def workflow_status_getter(execution_id, workflow_col: AsyncIOMotorCollection):
#     return await workflow_col.find_one({"execution_id": execution_id}, projection={"_id": False})
#
#
# async def node_status_getter(combined_id, node_col: AsyncIOMotorCollection):
#     return await node_col.find_one({"combined_id": combined_id}, projection={"_id": False})


# # results_stream = Blueprint('results_stream', __name__)
# workflow_stream_subs = set()
# action_stream_subs = set()
#
#
# async def push_to_workflow_stream_queue(workflow_status: WorkflowStatus, event):
#     if workflow_status.node_status is not None:
#         workflow_status.node_status = []
#     # workflow_status.pop("node_status", None)
#     workflow_status.execution_id = str(workflow_status.execution_id)
#     redis_stream = None
#     # sse_event_text = sse_format(data=workflow_status, event=event, event_id=workflow_status["execution_id"])
#     if workflow_status.execution_id in workflow_stream_subs:
#         redis_stream = WORKFLOW_STREAM_GLOB + "." + workflow_status.execution_id
#         # workflow_stream_subs[workflow_status["execution_id"]].put(sse_event_text)
#     if 'all' in workflow_stream_subs:
#         redis_stream = WORKFLOW_STREAM_GLOB + ".all"
#
#     if redis_stream is not None:
#         async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
#             key = f"{redis_stream}"
#             value = workflow_status.json()
#             # print(type(value))
#             await conn.lpush(key, value)
#
#
# async def push_to_action_stream_queue(node_status: NodeStatus, event):
#
#     for node_status in node_status:
#         node_status_json = node_status
#         node_status_json["execution_id"] = str(node_status_json["execution_id"])
#         execution_id = str(node_status_json["execution_id"])
#         # sse_event_text = sse_format(data=node_status_json, event=event, event_id=event_id)
#
#         if execution_id in action_stream_subs:
#             redis_stream = ACTION_STREAM_GLOB + "." + node_status_json["execution_id"]
#             # action_stream_subs[execution_id].put(sse_event_text)
#         elif 'all' in action_stream_subs:
#             redis_stream = ACTION_STREAM_GLOB + ".all"
#             # action_stream_subs['all'].put(sse_event_text)
#         else:
#             redis_stream = WORKFLOW_STREAM_GLOB + "." + node_status_json["execution_id"]
#             action_stream_subs.add(node_status_json["execution_id"])
#             redis_stream = ACTION_STREAM_GLOB + "." + node_status_json["execution_id"]
#
#         async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
#             key = f"{redis_stream}"
#             value = node_status_json
#             await conn.lpush(key, value)


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

# TODO SIO: this will become sio.on('workflow_status_update', namespaces=['/results'])
# TODO: maybe make an internal user for the worker/umpire?

#
# async def update_workflow_status(body: JSONPatch, event: str, execution_id: str,
#                                  workflow_col: AsyncIOMotorCollection = Depends((get_mongo_c)), close: str = None):
#     old_workflow = workflow_status_getter(execution_id, workflow_col)
#     old_workflow_status = old_workflow.status
#
#     # TODO: change these on the db model to be keyed by ID
#     if "node_status" in old_workflow_status:
#         old_workflow_status.node_status = {astat['node_id']: astat for astat in old_workflow_status.node_status}
#     else:
#         old_workflow_status.node_status = {}
#
#     patch = jsonpatch.JsonPatch.from_string(json.dumps(body))
#
#     logger.debug(f"Patch: {patch}")
#     logger.debug(f"Old Workflow Status: {old_workflow_status}")
#
#     new_workflow_status = patch.apply(old_workflow_status)
#
#     new_workflow_status.node_status = list(new_workflow_status.node_status.values())
#     if close is not None and close == "Done":
#         new_workflow_status.websocket_finished = True
#     else:
#         new_workflow_status.websocket_finished = False
#
#     try:
#         await workflow_col.replace_one(old_workflow, new_workflow_status)
#         # execution_id = workflow_status_schema.load(new_workflow_status, instance=execution_id)
#         # current_app.running_context.execution_db.session.commit()
#
#         node_status = []
#         for patch in body:
#             if "node_status" in patch["path"]:
#                 node_status.append(node_status_getter(patch["value"]["combined_id"]))
#
#         # TODo: Replace this when moving to sanic
#         logger.info(f"Workflow Status update: {new_workflow_status}")
#         await push_to_workflow_stream_queue(new_workflow_status, event)
#         # gevent.spawn(push_to_workflow_stream_queue, new_workflow_status, event)
#
#         if node_status:
#             logger.info(f"Action Status update:{node_status}")
#             await push_to_action_stream_queue(node_status, event)
#             # gevent.spawn(push_to_action_stream_queue, node_status, event)
#
#         logger.info(f"Updated workflow status {old_workflow.execution_id} ({old_workflow.name})")
#         return new_workflow_status
#     except Exception as e:
#         return UniquenessException('workflow status', 'update', old_workflow.id_)
#
#
# @router.websocket_route('/workflow_status/')
# async def workflow_stream(websocket: WebSocket, exec_id: Union[UUID, str] = "all"):
#     await websocket.accept()
#     redis_stream = WORKFLOW_STREAM_GLOB + "." + str(exec_id)
#     if exec_id not in workflow_stream_subs:
#         workflow_stream_subs.add(exec_id)
#     logger.info(f"workflow_status subscription for {exec_id}")
#     # if exec_id != 'all':
#     #     try:
#     #         uuid.UUID(exec_id)
#     #     except ValueError:
#     #         return invalid_id_problem('workflow status', 'read', exec_id)
#
#     async def workflow_results_generator():
#         async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
#             try:
#                 while True:
#                     await asyncio.sleep(1)
#                     event = conn.rpop(redis_stream)
#                     if event is not None:
#                         event_object = json.loads(event.decode("ascii"))
#                         message = event_object["message"]
#                         await websocket.send_text(message)
#                         logger.info(f"Sending workflow_status SSE for {exec_id}: {event}")
#                         if event_object["close"] == "Done":
#                             await conn.delete(redis_stream)
#                             workflow_stream_subs.remove(exec_id)
#                             await websocket.close(code=1000)
#             except Exception as e:
#                 await conn.delete(redis_stream)
#                 workflow_stream_subs.remove(exec_id)
#                 await websocket.close(code=1000)
#                 logger.info(f"Error: {e}")
#
#     return await workflow_results_generator()
#         # Response(workflow_results_generator(), mimetype="test/event-stream")
#
#
# @router.websocket_route('/actions/')
# async def action_stream(websocket: WebSocket, exec_id: Union[UUID, str] = "all"):
#     await websocket.accept()
#     redis_stream = ACTION_STREAM_GLOB + "." + str(exec_id)
#     if exec_id not in action_stream_subs:
#         action_stream_subs.add(exec_id)
#     logger.info(f"action subscription for {exec_id}")
#     # if execution_id != 'all':
#     #     try:
#     #         uuid.UUID(execution_id)
#     #     except ValueError:
#     #         return invalid_id_problem('action status', 'read', execution_id)
#
#     async def action_results_generator():
#         async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
#             try:
#                 while True:
#                     await asyncio.sleep(1)
#                     event = conn.rpop(redis_stream)
#                     if event is not None:
#                         event_object = json.loads(event.decode("ascii"))
#                         message = event_object["message"]
#                         await websocket.send_text(message)
#                         logger.info(f"Sending action websocket for for {exec_id}: {message}")
#                         if event_object["close"] == "Done":
#                             await conn.delete(redis_stream)
#                             action_stream_subs.remove(exec_id)
#                             await websocket.close(code=1000)
#             except Exception as e:
#                 await conn.delete(redis_stream)
#                 action_stream_subs.remove(exec_id)
#                 await websocket.close(code=1000)
#                 logger.info(f"Error: {e}")
#
#     return await action_results_generator()
