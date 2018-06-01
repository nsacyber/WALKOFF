from datetime import datetime
import sys
import json

from flask import current_app

from walkoff.events import WalkoffEvent
from walkoff.executiondb import ActionStatusEnum, WorkflowStatusEnum
from walkoff.executiondb.workflowresults import WorkflowStatus
from walkoff.helpers import convert_action_argument, utc_as_rfc_datetime
from walkoff.security import jwt_required_in_query
from walkoff.sse import SseStream, StreamableBlueprint

workflow_stream = SseStream('workflow_results')
action_stream = SseStream('action_results')

workflowresults_page = StreamableBlueprint('workflowresults_page', __name__, streams=(workflow_stream, action_stream))


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


@WalkoffEvent.ActionStarted.connect
@action_stream.push('started')
def action_started_callback(sender, **kwargs):
    return format_action_data(sender, kwargs, ActionStatusEnum.executing)


@WalkoffEvent.ActionExecutionSuccess.connect
@action_stream.push('success')
def action_ended_callback(sender, **kwargs):
    return format_action_data_with_results(sender, kwargs, ActionStatusEnum.success)


@WalkoffEvent.ActionExecutionError.connect
@action_stream.push('failure')
def action_error_callback(sender, **kwargs):
    return format_action_data_with_results(sender, kwargs, ActionStatusEnum.failure)


@WalkoffEvent.ActionArgumentsInvalid.connect
@action_stream.push('failure')
def action_args_invalid_callback(sender, **kwargs):
    return format_action_data_with_results(sender, kwargs, ActionStatusEnum.failure)


@WalkoffEvent.TriggerActionAwaitingData.connect
@action_stream.push('awaiting_data')
def trigger_awaiting_data_action_callback(sender, **kwargs):
    return format_action_data(sender, kwargs, ActionStatusEnum.awaiting_data)


def format_workflow_result(sender, status):
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
                      if field not in ('execution_id', 'workflow_id', 'name', 'status', 'current_action')):
            status_json.pop(field)
        status_json['timestamp'] = utc_as_rfc_datetime(datetime.utcnow())
        status_json['status'] = status.name  # in case this callback is called before it is properly set in the database
        return status_json
    return {
        'execution_id': str(workflow_execution_id),
        'timestamp': utc_as_rfc_datetime(datetime.utcnow()),
        'status': status.name}


@WalkoffEvent.WorkflowExecutionPending.connect
@workflow_stream.push('queued')
def workflow_pending_callback(sender, **kwargs):
    return format_workflow_result(sender, WorkflowStatusEnum.pending)


@WalkoffEvent.WorkflowExecutionStart.connect
@workflow_stream.push('started')
def workflow_started_callback(sender, **kwargs):
    return format_workflow_result(sender, WorkflowStatusEnum.running)


@WalkoffEvent.WorkflowPaused.connect
@workflow_stream.push('paused')
def workflow_paused_callback(sender, **kwargs):
    return format_workflow_result_with_current_step(sender['execution_id'], WorkflowStatusEnum.paused)


@WalkoffEvent.WorkflowResumed.connect
@workflow_stream.push('resumed')
def workflow_resumed_callback(sender, **kwargs):
    return format_workflow_result_with_current_step(sender.get_execution_id(), WorkflowStatusEnum.running)


@WalkoffEvent.TriggerActionAwaitingData.connect
@workflow_stream.push('awaiting_data')
def trigger_awaiting_data_workflow_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow']['execution_id']
    return format_workflow_result_with_current_step(workflow_execution_id, WorkflowStatusEnum.awaiting_data)


@WalkoffEvent.TriggerActionTaken.connect
@workflow_stream.push('triggered')
def trigger_action_taken_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow_execution_id']
    return format_workflow_result_with_current_step(workflow_execution_id, WorkflowStatusEnum.pending)


@WalkoffEvent.WorkflowAborted.connect
@workflow_stream.push('aborted')
def workflow_aborted_callback(sender, **kwargs):
    return format_workflow_result(sender, WorkflowStatusEnum.aborted)


@WalkoffEvent.WorkflowShutdown.connect
@workflow_stream.push('completed')
def workflow_shutdown_callback(sender, **kwargs):
    return format_workflow_result(sender, WorkflowStatusEnum.completed)


@workflowresults_page.route('/actions', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_action_events():
    return action_stream.stream()


@workflowresults_page.route('/workflow_status', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_status():
    return workflow_stream.stream()
