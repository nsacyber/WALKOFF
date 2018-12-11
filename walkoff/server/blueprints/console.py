import logging
from uuid import UUID

from flask import request

from walkoff.events import WalkoffEvent
from walkoff.security import jwt_required_in_query
from walkoff.server.problem import Problem
from walkoff.server.returncodes import BAD_REQUEST
from walkoff.sse import FilteredSseStream, StreamableBlueprint

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


@WalkoffEvent.ConsoleLog.connect
@console_stream.push('log')
def console_log_callback(sender, **kwargs):
    return format_console_data(sender, kwargs["data"]), sender['execution_id']


@console_page.route('/log', methods=['GET'])
@jwt_required_in_query('access_token')
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
