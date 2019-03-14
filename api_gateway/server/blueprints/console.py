import logging
from uuid import UUID
from http import HTTPStatus
import json

import gevent
from gevent.lock import RLock
from gevent.queue import Queue
from flask import Blueprint, Response, current_app, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_claims

from api_gateway.server.problem import Problem
from api_gateway.server.problem import invalid_id_problem

console_page = Blueprint('console_page', __name__)
console_stream_subs = {}
console_stream_lock = RLock()


@console_page.route('/log', methods=['POST'])
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions("consolelog", ["create"]))
def create_console_message():
    workflow_execution_id = request.args.get('workflow_execution_id', 'all')
    message_json = request.get_json()

    if workflow_execution_id in console_stream_subs:
        gevent.spawn(console_stream_subs[workflow_execution_id].put, json.dumps(message_json))
        current_app.logger.info(f"Pushed console log message.")

    return jsonify({"execution_id": workflow_execution_id, "message": message_json}), HTTPStatus.ACCEPTED


def format_console_data(sender, data):
    try:
        level = int(data['level'])
    except ValueError:
        level = data['level']
    return {
        'workflow': sender['name'],
        'app_name': data['app_name'],
        'name': data['name'],
        'level': logging.getLevelName(level),
        'message': data['message']
    }


def console_log_generator(execution_id):
    with console_stream_lock:
        console_stream_subs[execution_id] = events = console_stream_subs.get(execution_id, Queue())
    try:
        while True:
            yield events.get().encode()
    except GeneratorExit:
        with console_stream_lock:
            console_stream_subs.pop(events)


@console_page.route('/log', methods=['GET'])
# @jwt_required
def stream_console_events():
    workflow_execution_id = request.args.get('workflow_execution_id')
    if workflow_execution_id is None:
        return Problem(HTTPStatus.BAD_REQUEST, 'Could not connect to log stream',
                       'workflow_execution_id is a required query param')
    try:
        UUID(workflow_execution_id)
    except ValueError:
        return invalid_id_problem('workflow status', 'read', workflow_execution_id)

    return Response(console_log_generator(workflow_execution_id), mimetype="text/event-stream")
