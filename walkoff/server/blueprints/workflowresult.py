from datetime import datetime

from flask import Blueprint
from walkoff.events import WalkoffEvent
from walkoff.helpers import convert_action_argument
from walkoff.security import jwt_required_in_query
from walkoff.sse import SseStream

workflowresults_page = Blueprint('workflowresults_page', __name__)

sse_stream = SseStream('workflow_results')


def format_workflow_result(sender, **kwargs):
    action_arguments = [convert_action_argument(argument) for argument in sender.get('arguments', [])]
    return {'action_name': sender['name'],
            'action_uid': sender['uid'],
            'timestamp': str(datetime.utcnow()),
            'arguments': action_arguments,
            'result': kwargs['data']['result'],
            'status': kwargs['data']['status']}


@WalkoffEvent.ActionExecutionSuccess.connect
@sse_stream.push('action_success')
def action_ended_callback(sender, **kwargs):
    return format_workflow_result(sender, **kwargs)


@WalkoffEvent.ActionExecutionError.connect
@sse_stream.push('action_error')
def action_error_callback(sender, **kwargs):
    return format_workflow_result(sender, **kwargs)


@workflowresults_page.route('/stream', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_action_events():
    return sse_stream.stream()
