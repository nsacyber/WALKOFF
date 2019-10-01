import logging
from uuid import UUID
from http import HTTPStatus

import gevent
from gevent.queue import Queue
from flask import Blueprint, Response, request, jsonify

from api_gateway.helpers import sse_format
from api_gateway.server.problem import invalid_id_problem

build_stream = Blueprint('build_stream', __name__)
console_stream_subs = {}

logger = logging.getLogger(__name__)


def push_to_build_stream_queue(console_message, build_id):
    sse_event_text = sse_format(data=console_message, event='log', event_id=build_id)
    if build_id not in console_stream_subs:
        console_stream_subs[build_id] = Queue()

    console_stream_subs[build_id].put(sse_event_text)
    # if 'all' in console_stream_subs:
    #     console_stream_subs['all'].put(sse_event_text)


@build_stream.route('/build_logger', methods=['POST'])
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions("consolelog", ["create"]))
def create_console_message():
    build_id = request.args.get('build_id')
    message = request.get_json()
    logger.info(f"App console log: {message}")
    gevent.spawn(push_to_build_stream_queue, message, build_id)

    return jsonify(message), HTTPStatus.OK


@build_stream.route('/build_log', methods=['GET'])
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions("consolelog", ["create"]))
def read_console_message():
    build_id = request.args.get('build_id')
    logger.info(f"console log subscription for {build_id}")
    # if build_id != 'all':
    #     try:
    #         UUID(build_id)
    #     except ValueError:
    #         return invalid_id_problem('console log', 'read', build_id)

    def console_log_generator():
        console_stream_subs[build_id] = events = console_stream_subs.get(build_id, Queue())
        try:
            while True:
                event = events.get().encode()
                logger.info(f"Sending console message for {build_id}: {event}")
                yield event
        except GeneratorExit:
            console_stream_subs.pop(build_id)
            logger.info(f"console log unsubscription for {build_id}")

    return Response(console_log_generator(), mimetype="text/event-stream")

