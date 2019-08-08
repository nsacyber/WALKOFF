import logging
from uuid import UUID
from http import HTTPStatus

import gevent
from gevent.lock import RLock
from gevent.queue import Queue
from flask import Blueprint, Response, current_app, request, jsonify

from api_gateway.helpers import sse_format
from api_gateway.server.problem import invalid_id_problem

console_stream = Blueprint('console_stream', __name__)
console_stream_subs = {}

logger = logging.getLogger(__name__)


def push_to_console_stream_queue(console_message, execution_id):
    sse_event_text = sse_format(data=console_message, event='log', event_id=execution_id)
    if execution_id in console_stream_subs:
        console_stream_subs[execution_id].put(sse_event_text)
    if 'all' in console_stream_subs:
        console_stream_subs['all'].put(sse_event_text)


@console_stream.route('/logger', methods=['POST'])
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions("consolelog", ["create"]))
def create_console_message():
    workflow_execution_id = request.args.get('workflow_execution_id', 'all')
    message = request.get_json()
    logger.info(f"App console log: {message}")
    gevent.spawn(push_to_console_stream_queue, message, workflow_execution_id)

    return jsonify(message), HTTPStatus.OK


@console_stream.route('/log', methods=['GET'])
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions("consolelog", ["create"]))
def read_console_message():
    execution_id = request.args.get('workflow_execution_id', 'all')
    logger.info(f"console log subscription for {execution_id}")
    if execution_id != 'all':
        try:
            UUID(execution_id)
        except ValueError:
            return invalid_id_problem('console log', 'read', execution_id)

    def console_log_generator():
        console_stream_subs[execution_id] = events = console_stream_subs.get(execution_id, Queue())
        try:
            while True:
                event = events.get().encode()
                logger.info(f"Sending console message for {execution_id}: {event}")
                yield event
        except GeneratorExit:
            console_stream_subs.pop(execution_id)
            logger.info(f"console log unsubscription for {execution_id}")

    return Response(console_log_generator(), mimetype="text/event-stream")


#
# def format_console_data(sender, data):
#     try:
#         level = int(data['level'])
#     except ValueError:
#         level = data['level']
#     return {
#         'workflow': sender['name'],
#         'app_name': data['app_name'],
#         'name': data['name'],
#         'level': logging.getLevelName(level),
#         'message': data['message']
#     }
#
