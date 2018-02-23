from datetime import datetime

from flask import Blueprint, Response
from gevent import sleep
from gevent.event import Event, AsyncResult

from walkoff.events import WalkoffEvent
from walkoff.helpers import convert_action_argument, create_sse_event
from walkoff.security import jwt_required_in_query
from walkoff.coredb import ActionStatusEnum, WorkflowStatusEnum
from walkoff.coredb.workflowresults import WorkflowStatus
import walkoff.coredb.devicedb as devicedb

workflowqueue_page = Blueprint('workflowqueue_page', __name__)

__action_event_json = AsyncResult()
__action_signal = Event()

__action_event_id_counter = 0

__workflow_event_json = AsyncResult()
__workflow_signal = Event()

__workflow_event_id_counter = 0


def __action_event_stream():
    global __action_event_id_counter
    __action_signal.wait()
    while True:
        event_type, data = __action_event_json.get()
        yield create_sse_event(event_id=__action_event_id_counter, event=event_type, data=data)
        __action_event_id_counter += 1
        __action_signal.wait()


def __workflow_event_stream():
    global __workflow_event_id_counter
    __workflow_signal.wait()
    while True:
        event_type, data = __workflow_event_json.get()
        yield create_sse_event(event_id=__workflow_event_id_counter, event=event_type, data=data)
        __workflow_event_id_counter += 1
        __workflow_signal.wait()


def format_action_data(sender, kwargs, timestamp_type, status):
    action_arguments = [convert_action_argument(argument) for argument in sender.get('arguments', [])]
    return {'action_name': sender['action_name'],
            'app_name': sender['app_name'],
            'action_id': sender['id'],
            'name': sender['name'],
            'execution_id': sender['execution_id'],
            timestamp_type: datetime.utcnow().isoformat(),
            'status': status.name,
            'arguments': action_arguments,
            'workflow_execution_id': kwargs['data']['workflow']['execution_id']}


def format_action_data_with_results(sender, kwargs, timestamp_type, status):
    result = format_action_data(sender, kwargs, timestamp_type, status)
    result['result'] = kwargs['data']['data']['result']
    return result


def send_action_result_to_sse(result, event):
    __action_event_json.set((event, result))
    sleep(0)
    __action_signal.set()
    __action_signal.clear()
    sleep(0)


@WalkoffEvent.ActionStarted.connect
def __action_started_callback(sender, **kwargs):
    result = format_action_data(sender, kwargs, 'started_at', ActionStatusEnum.executing)
    send_action_result_to_sse(result, 'started')


@WalkoffEvent.ActionExecutionSuccess.connect
def __action_ended_callback(sender, **kwargs):
    result = format_action_data_with_results(sender, kwargs, 'completed_at', ActionStatusEnum.success)
    send_action_result_to_sse(result, 'success')


@WalkoffEvent.ActionExecutionError.connect
def __action_error_callback(sender, **kwargs):
    __handle_action_error(sender, kwargs)


@WalkoffEvent.ActionArgumentsInvalid.connect
def __action_args_invalid_callback(sender, **kwargs):
    __handle_action_error(sender, kwargs)


def __handle_action_error(sender, kwargs):
    result = format_action_data_with_results(sender, kwargs, 'completed_at', ActionStatusEnum.failure)
    send_action_result_to_sse(result, 'failure')


def format_workflow_result(sender, status):
    return {'execution_id': str(sender['execution_id']),
            'workflow_id': str(sender['id']),
            'name': sender['name'],
            'status': status.name,
            'timestamp': datetime.utcnow().isoformat()}


def format_workflow_result_from_workflow(sender, status):
    result = {'execution_id': str(sender.get_execution_id()),
              'workflow_id': str(sender.id),
              'name': sender.name,
              'status': status.name,
              'timestamp': datetime.utcnow().isoformat()}
    return result


def format_workflow_result_with_current_step(workflow_execution_id, status):
    workflow_status = devicedb.device_db.session.query(WorkflowStatus).filter_by(
        execution_id=workflow_execution_id).first()
    if workflow_status is not None:
        status_json = workflow_status.as_json()
        for field in (field for field in status_json.keys()
                      if field not in ('execution_id', 'workflow_id', 'name', 'status', 'current_action')):
            status_json.pop(field)
        status_json['timestamp'] = datetime.utcnow().isoformat()
        status_json['status'] = status.name  # in case this callback is called before it is properly set in the database
        return status_json
    return {'execution_id': str(workflow_execution_id), 'status': status.name}


def send_workflow_result_to_sse(result, event):
    __workflow_event_json.set((event, result))
    sleep(0)
    __workflow_signal.set()
    __workflow_signal.clear()
    sleep(0)


@WalkoffEvent.WorkflowExecutionPending.connect
def __workflow_pending_callback(sender, **kwargs):
    result = format_workflow_result_from_workflow(sender, WorkflowStatusEnum.pending)
    send_workflow_result_to_sse(result, 'queued')


@WalkoffEvent.WorkflowExecutionStart.connect
def __workflow_started_callback(sender, **kwargs):
    result = format_workflow_result(sender, WorkflowStatusEnum.running)
    send_workflow_result_to_sse(result, 'started')


@WalkoffEvent.WorkflowPaused.connect
def __workflow_paused_callback(sender, **kwargs):
    result = format_workflow_result_with_current_step(sender['execution_id'], WorkflowStatusEnum.paused)
    send_workflow_result_to_sse(result, 'paused')


@WalkoffEvent.WorkflowResumed.connect
def __workflow_resumed_callback(sender, **kwargs):
    result = format_workflow_result_with_current_step(sender.get_execution_id(), WorkflowStatusEnum.running)
    send_workflow_result_to_sse(result, 'resumed')


@WalkoffEvent.TriggerActionAwaitingData.connect
def __trigger_awaiting_data_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow']['execution_id']
    result = format_workflow_result_with_current_step(workflow_execution_id, WorkflowStatusEnum.awaiting_data)
    send_workflow_result_to_sse(result, 'awaiting_data')


@WalkoffEvent.TriggerActionTaken.connect
def __trigger_action_taken_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow_execution_id']
    result = format_workflow_result_with_current_step(workflow_execution_id, WorkflowStatusEnum.pending)
    send_workflow_result_to_sse(result, 'triggered')


@WalkoffEvent.WorkflowAborted.connect
def __workflow_aborted_callback(sender, **kwargs):
    result = format_workflow_result(sender, WorkflowStatusEnum.aborted)
    send_workflow_result_to_sse(result, 'aborted')


@WalkoffEvent.WorkflowShutdown.connect
def __workflow_shutdown_callback(sender, **kwargs):
    result = format_workflow_result(sender, WorkflowStatusEnum.completed)
    send_workflow_result_to_sse(result, 'completed')


@workflowqueue_page.route('/actions', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_action_events():
    return Response(__action_event_stream(), mimetype='text/event-stream')


@workflowqueue_page.route('/workflow_status', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_status():
    return Response(__workflow_event_stream(), mimetype='text/event-stream')
