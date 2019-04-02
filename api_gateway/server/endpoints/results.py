import re
import uuid
import json
from http import HTTPStatus
from datetime import datetime

import gevent
from gevent.queue import Queue

from flask import Blueprint, Response, current_app, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_claims

from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, StatementError

import jsonpatch

from api_gateway.server.decorators import with_resource_factory, paginate, is_valid_uid
from api_gateway.executiondb.workflow import Workflow, WorkflowSchema
from api_gateway.executiondb.workflowresults import (WorkflowStatus, ActionStatus, WorkflowStatusSchema,
                                                     ActionStatusSchema)

from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.problem import unique_constraint_problem, improper_json_problem, invalid_id_problem
from api_gateway.sse import SseEvent


def workflow_getter(workflow_id):
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id_=workflow_id).first()


def workflow_status_getter(execution_id):
    return current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=execution_id).first()


def action_status_getter(combined_id):
    return current_app.running_context.execution_db.session.query(ActionStatus).filter_by(
        combined_id=combined_id).first()


with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)
with_workflow_status = with_resource_factory('workflow', workflow_status_getter, validator=is_valid_uid)

action_status_schema = ActionStatusSchema()
workflow_status_schema = WorkflowStatusSchema()

results_stream = Blueprint('results_stream', __name__)
workflow_stream_subs = {}
action_stream_subs = {}


def push_to_workflow_stream_queue(workflow_status, event):
    workflow_status.pop("action_statuses", None)
    sse_event_text = SseEvent(event, workflow_status).format(workflow_status["execution_id"])

    if workflow_status["execution_id"] in workflow_stream_subs:
        workflow_stream_subs[workflow_status["execution_id"]].put(sse_event_text)
    if 'all' in workflow_stream_subs:
        workflow_stream_subs['all'].put(sse_event_text)


def push_to_action_stream_queue(action_statuses, event):
    event_id = 0
    for action_status in action_statuses:
        action_status_json = action_status_schema.dump(action_status)
        sse_event = SseEvent(event, action_status_json)
        execution_id = str(action_status_json["execution_id"])
        if execution_id in action_stream_subs:
            action_stream_subs[execution_id].put(sse_event.format(event_id))
        event_id += 1


# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions("workflowstatus", ["create"]))
# def create_workflow_status():
#     workflow_status_json = request.get_json()
#     workflow_id = workflow_status_json.get("workflow_id")
#     workflow = workflow_getter(workflow_id)
#     print(workflow_id)
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
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions("workflowstatus", ["create"]))
@with_workflow_status('update', 'execution_id')
def update_workflow_status(execution_id):
    old_workflow_status = workflow_status_schema.dump(execution_id)
    data = request.get_json()

    # TODO: change these on the db model to be keyed by ID
    if "action_statuses" in old_workflow_status:
        old_workflow_status["action_statuses"] = {astat['action_id']: astat for astat in
                                                  old_workflow_status["action_statuses"]}
    else:
        old_workflow_status["action_statuses"] = {}

    patch = jsonpatch.JsonPatch.from_string(json.dumps(data))
    new_workflow_status = patch.apply(old_workflow_status)

    new_workflow_status["action_statuses"] = list(new_workflow_status["action_statuses"].values())

    resource = request.args.get("resource")
    event = request.args.get("event")

    try:
        execution_id = workflow_status_schema.load(new_workflow_status, instance=execution_id)

        current_app.running_context.execution_db.session.commit()

        action_statuses = []
        for patch in data:
            if "action_statuses" in patch["path"]:
                action_statuses.append(action_status_getter(patch["value"]["combined_id"]))

        # TODo: Replace this when moving to sanic
        if len(action_statuses) < 1:
            gevent.spawn(push_to_workflow_stream_queue, new_workflow_status, event)
        else:
            gevent.spawn(push_to_action_stream_queue, action_statuses, event)

        current_app.logger.info(f"Updated workflow status {execution_id.execution_id} ({execution_id.name})")
        return workflow_status_schema.dump(execution_id), HTTPStatus.OK
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem('workflow status', 'update', execution_id.id_)


@results_stream.route('/workflow_status')
def workflow_stream():
    execution_id = request.args.get('workflow_execution_id', 'all')
    if execution_id != 'all':
        try:
            uuid.UUID(execution_id)
        except ValueError:
            return invalid_id_problem('workflow status', 'read', execution_id)

    def workflow_results_generator():
        workflow_stream_subs[execution_id] = events = workflow_stream_subs.get(execution_id, Queue())
        try:
            while True:
                yield events.get().encode()
        except GeneratorExit:
            workflow_stream_subs.pop(events)

    return Response(workflow_results_generator(), mimetype="test/event-stream")


@results_stream.route('/actions')
def action_stream():
    execution_id = request.args.get('workflow_execution_id', 'all')
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
                print(event)
                yield event
        except GeneratorExit:
            action_stream_subs.pop(execution_id)

    return Response(action_results_generator(), mimetype="text/event-stream")
