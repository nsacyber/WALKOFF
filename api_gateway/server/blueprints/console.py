import logging
from uuid import UUID

from flask import request
from flask_jwt_extended import jwt_required

from api_gateway.events import WalkoffEvent
from api_gateway.server.problem import Problem
from api_gateway.server.returncodes import BAD_REQUEST
from api_gateway.sse import FilteredSseStream, StreamableBlueprint

console_stream = FilteredSseStream('console_results')
console_page = StreamableBlueprint('console_page', __name__, streams=(console_stream,))


def format_console_data(sender, data):
    try:
        level = int(data['level'])
    except ValueError:
        level = data['level']
    return {
        'workflow': sender['name'],
        'app_name': data['app_name'],
        'action_name': data['action_name'],
        'level': logging.getLevelName(level),
        'message': data['message']
    }


# TODO: Make console logging pub/sub pipeline for currently executing actions
# something like a "app-logger" channel handling {"execution_id": exid, "message": "hello world!"} type messages
@WalkoffEvent.ConsoleLog.connect
@console_stream.push('log')
def console_log_callback(sender, **kwargs):
    return format_console_data(sender, kwargs["data"]), sender['execution_id']


@console_page.route('/log', methods=['GET'])
@jwt_required
def stream_console_events():
    workflow_execution_id = request.args.get('workflow_execution_id')
    if workflow_execution_id is None:
        return Problem(
            BAD_REQUEST,
            'Could not connect to log stream',
            'workflow_execution_id is a required query param')
    try:
        UUID(workflow_execution_id)
        return console_stream.stream(subchannel=workflow_execution_id)
    except (ValueError, AttributeError):
        return Problem(
            BAD_REQUEST,
            'Could not connect to log stream',
            'workflow_execution_id must be a valid UUID')
