from datetime import datetime
from uuid import UUID

from enum import Enum, unique
from flask import current_app, request
from flask_jwt_extended import jwt_required

from api_gateway.events import WalkoffEvent
from api_gateway.executiondb import ActionStatusEnum, WorkflowStatusEnum
from api_gateway.executiondb.workflowresults import WorkflowStatus
from api_gateway.helpers import convert_action_argument, utc_as_rfc_datetime
from api_gateway.server.problem import Problem
from api_gateway.server.returncodes import BAD_REQUEST
from api_gateway.sse import FilteredSseStream, StreamableBlueprint

workflow_stream = FilteredSseStream('workflow_results')
action_stream = FilteredSseStream('action_results')
action_summary_stream = FilteredSseStream('action_results_summary')

workflowresults_page = StreamableBlueprint(
    'workflowresults_page',
    __name__,
    streams=(workflow_stream, action_stream, action_summary_stream)
)

action_summary_keys = ('action_name', 'app_name', 'action_id', 'name', 'timestamp', 'workflow_execution_id')


@unique
class ActionStreamEvent(Enum):
    started = 1
    success = 2
    failure = 3
    awaiting_data = 4


def format_action_data(sender, kwargs, status):
    action_arguments = [convert_action_argument(argument) for argument in sender.get('arguments', [])]
    return {'action_name': sender['action_name'],
            'app_name': sender['app_name'],
            'action_id': sender['id'],
            'name': sender['name'],
            'execution_id': sender['execution_id'],
            'timestamp': utc_as_rfc_datetime(datetime.utcnow()),
            'status': status.name,
            'arguments': action_arguments,
            'workflow_execution_id': kwargs['data']['workflow']['execution_id']}


def format_action_data_with_results(sender, kwargs, status):
    result = format_action_data(sender, kwargs, status)
    action_result = kwargs['data']['data']['result']
    with current_app.app_context():
        max_len = current_app.config['MAX_STREAM_RESULTS_SIZE_KB'] * 1024
    result_str = str(action_result)
    if len(result_str) > max_len:
        result['result'] = {'truncated': result_str[:max_len]}
    else:
        result['result'] = action_result
    return result


def format_action_return(data, event):
    return data, (data['workflow_execution_id'], 'all'), event


@action_stream.push(None)
def push_to_action_stream(data, event):
    return format_action_return(data, event)


@action_summary_stream.push(None)
def push_to_action_summary_stream(data, event):
    data = {key: data[key] for key in action_summary_keys}
    return format_action_return(data, event)


@WalkoffEvent.ActionStarted.connect
def action_started_callback(sender, **kwargs):
    data = format_action_data(sender, kwargs, ActionStatusEnum.executing)
    push_to_action_stream(data, ActionStreamEvent.started.name)
    push_to_action_summary_stream(data, ActionStreamEvent.started.name)


@WalkoffEvent.ActionExecutionSuccess.connect
def action_ended_callback(sender, **kwargs):
    data = format_action_data_with_results(sender, kwargs, ActionStatusEnum.success)
    push_to_action_stream(data, ActionStreamEvent.success.name)
    push_to_action_summary_stream(data, ActionStreamEvent.success.name)


@WalkoffEvent.ActionExecutionError.connect
@WalkoffEvent.ActionArgumentsInvalid.connect
def action_error_callback(sender, **kwargs):
    data = format_action_data_with_results(sender, kwargs, ActionStatusEnum.failure)
    push_to_action_stream(data, ActionStreamEvent.failure.name)
    push_to_action_summary_stream(data, ActionStreamEvent.failure.name)


@WalkoffEvent.TriggerActionAwaitingData.connect
def trigger_awaiting_data_action_callback(sender, **kwargs):
    data = format_action_data(sender, kwargs, ActionStatusEnum.awaiting_data)
    push_to_action_stream(data, ActionStreamEvent.awaiting_data.name)
    push_to_action_summary_stream(data, ActionStreamEvent.awaiting_data.name)


@unique
class WorkflowStreamEvent(Enum):
    queued = 1
    started = 2
    paused = 3
    resumed = 4
    awaiting_data = 5
    triggered = 6
    aborted = 7
    completed = 8


def format_workflow_result(sender, status):
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    if workflow_status is not None:
        return {'execution_id': str(sender['execution_id']),
                'workflow_id': str(sender['id']),
                'name': sender['name'],
                'status': status.name,
                'timestamp': utc_as_rfc_datetime(datetime.utcnow()),
                'user': workflow_status.user}
    return {'execution_id': str(sender['execution_id']),
            'workflow_id': str(sender['id']),
            'name': sender['name'],
            'status': status.name,
            'timestamp': utc_as_rfc_datetime(datetime.utcnow())}


def format_workflow_result_with_current_step(workflow_execution_id, status):
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=workflow_execution_id).first()
    if workflow_status is not None:
        status_json = workflow_status.as_json()
        for field in (field for field in list(status_json.keys())
                      if field not in ('execution_id', 'workflow_id', 'name', 'status', 'current_action', 'user')):
            status_json.pop(field)
        status_json['timestamp'] = utc_as_rfc_datetime(datetime.utcnow())
        status_json['status'] = status.name  # in case this callback is called before it is properly set in the database
        return status_json
    return {
        'execution_id': str(workflow_execution_id),
        'timestamp': utc_as_rfc_datetime(datetime.utcnow()),
        'status': status.name}


def format_workflow_return(data):
    return data, (data['execution_id'], 'all')


@WalkoffEvent.WorkflowExecutionPending.connect
@workflow_stream.push(WorkflowStreamEvent.queued.name)
def workflow_pending_callback(sender, **kwargs):
    data = format_workflow_result(sender, WorkflowStatusEnum.pending)
    return format_workflow_return(data)


@WalkoffEvent.WorkflowExecutionStart.connect
@workflow_stream.push(WorkflowStreamEvent.started.name)
def workflow_started_callback(sender, **kwargs):
    data = format_workflow_result(sender, WorkflowStatusEnum.running)
    return format_workflow_return(data)


@WalkoffEvent.WorkflowPaused.connect
@workflow_stream.push(WorkflowStreamEvent.paused.name)
def workflow_paused_callback(sender, **kwargs):
    data = format_workflow_result_with_current_step(sender['execution_id'], WorkflowStatusEnum.paused)
    return format_workflow_return(data)


@WalkoffEvent.WorkflowResumed.connect
@workflow_stream.push(WorkflowStreamEvent.resumed.name)
def workflow_resumed_callback(sender, **kwargs):
    data = format_workflow_result_with_current_step(kwargs['data']['execution_id'], WorkflowStatusEnum.running)
    return format_workflow_return(data)


@WalkoffEvent.TriggerActionAwaitingData.connect
@workflow_stream.push(WorkflowStreamEvent.awaiting_data.name)
def trigger_awaiting_data_workflow_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow']['execution_id']
    data = format_workflow_result_with_current_step(workflow_execution_id, WorkflowStatusEnum.awaiting_data)
    return format_workflow_return(data)


@WalkoffEvent.TriggerActionTaken.connect
@workflow_stream.push(WorkflowStreamEvent.triggered.name)
def trigger_action_taken_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow_execution_id']
    data = format_workflow_result_with_current_step(workflow_execution_id, WorkflowStatusEnum.pending)
    return format_workflow_return(data)


@WalkoffEvent.WorkflowAborted.connect
@workflow_stream.push(WorkflowStreamEvent.aborted.name)
def workflow_aborted_callback(sender, **kwargs):
    data = format_workflow_result(sender, WorkflowStatusEnum.aborted)
    return format_workflow_return(data)


@WalkoffEvent.WorkflowShutdown.connect
@workflow_stream.push(WorkflowStreamEvent.completed.name)
def workflow_shutdown_callback(sender, **kwargs):
    data = format_workflow_result(sender, WorkflowStatusEnum.completed)
    return format_workflow_return(data)


# JWT now required in header instead of query string
@workflowresults_page.route('/actions', methods=['GET'])
@jwt_required
def stream_workflow_action_events():
    workflow_execution_id = request.args.get('workflow_execution_id', 'all')
    if workflow_execution_id != 'all':
        try:
            UUID(workflow_execution_id)
        except ValueError:
            return Problem(
                BAD_REQUEST,
                'Could not connect to action results stream',
                'workflow_execution_id must be a valid UUID')
    if request.args.get('summary'):
        return action_summary_stream.stream(subchannel=workflow_execution_id)
    else:
        return action_stream.stream(subchannel=workflow_execution_id)


@workflowresults_page.route('/workflow_status', methods=['GET'])
@jwt_required
def stream_workflow_status():
    workflow_execution_id = request.args.get('workflow_execution_id', 'all')
    if workflow_execution_id != 'all':
        try:
            UUID(workflow_execution_id)
        except ValueError:
            return Problem(
                BAD_REQUEST,
                'Could not connect to action results stream',
                'workflow_execution_id must be a valid UUID')
    return workflow_stream.stream(subchannel=workflow_execution_id)
