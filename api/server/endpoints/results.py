import uuid
import json
from uuid import UUID
import logging
import gevent
from gevent.queue import Queue

from motor.motor_asyncio import AsyncIOMotorCollection
from flask import Blueprint, Response, current_app, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from api.server.utils.problems import UniquenessException
import jsonpatch

from api.server.utils.helpers import sse_format
from api.server.db import get_mongo_c
from api.server.db.workflowresults import WorkflowStatus, NodeStatus
from starlette.websockets import WebSocket

from fastapi import APIRouter, Depends, HTTPException

from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.problem import unique_constraint_problem, invalid_id_problem

logger = logging.getLogger(__name__)
router = APIRouter()


class JSONPatch(BaseModel):
    op: str
    path: str
    value: str
    start: str


def workflow_status_getter(execution_id, workflow_col: AsyncIOMotorCollection):
    return await workflow_col.find_one({"execution_id": execution_id}, projection={"_id": False})


def node_status_getter(combined_id, node_col: AsyncIOMotorCollection):
    return await node_col.find_one({"combined_id": combined_id}, projection={"_id": False})


results_stream = Blueprint('results_stream', __name__)
workflow_stream_subs = {}
action_stream_subs = {}


def push_to_workflow_stream_queue(workflow_status, event):
    workflow_status.pop("node_statuses", None)
    workflow_status["execution_id"] = str(workflow_status["execution_id"])
    sse_event_text = sse_format(data=workflow_status, event=event, event_id=workflow_status["execution_id"])
    if workflow_status["execution_id"] in workflow_stream_subs:
        workflow_stream_subs[workflow_status["execution_id"]].put(sse_event_text)
    if 'all' in workflow_stream_subs:
        workflow_stream_subs['all'].put(sse_event_text)


def push_to_action_stream_queue(node_statuses, event):

    event_id = 0
    for node_status in node_statuses:
        node_status_json = node_status_schema.dump(node_status)
        node_status_json["execution_id"] = str(node_status_json["execution_id"])
        execution_id = str(node_status_json["execution_id"])
        sse_event_text = sse_format(data=node_status_json, event=event, event_id=event_id)

        if execution_id in action_stream_subs:
            action_stream_subs[execution_id].put(sse_event_text)
        if 'all' in action_stream_subs:
            action_stream_subs['all'].put(sse_event_text)
        event_id += 1


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
def update_workflow_status(body: JSONPatch, event: str, execution_id: str, workflow_col: AsyncIOMotorCollection = Depends((get_mongo_c))):
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
        gevent.spawn(push_to_workflow_stream_queue, new_workflow_status, event)

        if node_statuses:
            logger.info(f"Action Status update:{node_statuses}")
            gevent.spawn(push_to_action_stream_queue, node_statuses, event)

        logger.info(f"Updated workflow status {old_workflow.execution_id} ({old_workflow.name})")
        return new_workflow_status
    except IntegrityError:
        return UniquenessException('workflow status', 'update', old_workflow.id_)


@router.websocket_route('/workflow_status')
def workflow_stream(websocket: WebSocket, exec_id: UUID = None):
    await websocket.accept()
    execution_id = exec_id
    logger.info(f"workflow_status subscription for {execution_id}")
    if execution_id != 'all':
        try:
            uuid.UUID(execution_id)
        except ValueError:
            return invalid_id_problem('workflow status', 'read', execution_id)

    def workflow_results_generator():
        workflow_stream_subs[execution_id] = events = workflow_stream_subs.get(execution_id, Queue())
        try:
            while True:
                event = events.get().encode()
                logger.info(f"Sending workflow_status SSE for {execution_id}: {event}")
                await websocket.send_text(event)
        except GeneratorExit:
            workflow_stream_subs.pop(events, None)
            await websocket.close(code=1000)
            logger.info(f"workflow_status unsubscription for {execution_id}")

    return Response(workflow_results_generator(), mimetype="test/event-stream")


@router.websocket_route('/actions')
def action_stream(websocket: WebSocket, exec_id: UUID = None):
    await websocket.accept()
    execution_id = exec_id
    logger.info(f"action subscription for {execution_id}")
    if execution_id != 'all':
        try:
            uuid.UUID(execution_id)
        except ValueError:
            return invalid_id_problem('action status', 'read', execution_id)

    def action_results_generator():
        action_stream_subs[execution_id] = events = action_stream_subs.get(execution_id, Queue())
        try:
            while True:
                event = events.get().encode()
                logger.info(f"Sending action SSE for {execution_id}: {event}")
                await websocket.send_text(event)
        except GeneratorExit:
            action_stream_subs.pop(execution_id, None)
            await websocket.close(code=1000)
            logger.info(f"action unsubscription for {execution_id}")

    return Response(action_results_generator(), mimetype="text/event-stream")
