import logging
from uuid import UUID
from http import HTTPStatus
import json

import gevent
from gevent.lock import RLock
from gevent.queue import Queue
from flask import Blueprint, Response, current_app, request, jsonify

from api_gateway.server.problem import Problem
from api_gateway.server.problem import invalid_id_problem

console_page = Blueprint('console_page', __name__)
console_stream_subs = {}
console_stream_lock = RLock()


@console_page.route('/log')
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions("consolelog", ["create"]))
def create_console_message():
    workflow_execution_id = request.args.get('workflow_execution_id', 'all')
    message_json = request.get_json()
    if workflow_execution_id in console_stream_subs:
        gevent.spawn(console_stream_subs[workflow_execution_id].put, json.dumps(message_json))
        current_app.logger.debug(f"Pushed console log message: {json.dumps(message_json)}")

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
            event = events.get().encode()
            current_app.logger.info(f"Sending console message for {execution_id}: {event}")
            yield event
    except GeneratorExit:
        with console_stream_lock:
            console_stream_subs.pop(events)
            current_app.logger.info(f"console log unsubscription for {execution_id}")


@console_page.route('/log', methods=['GET'])
# @jwt_required
def stream_console_events():
    execution_id = request.args.get('workflow_execution_id')
    current_app.logger.debug(f"console log subscription for {execution_id}")
    if execution_id != 'all':
        try:
            UUID(execution_id)
        except ValueError:
            return invalid_id_problem('console log', 'read', execution_id)

    return Response(console_log_generator(execution_id), mimetype="text/event-stream")
