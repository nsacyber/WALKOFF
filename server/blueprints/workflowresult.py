from datetime import datetime

from flask import Blueprint, Response
from gevent import sleep
from gevent.event import Event, AsyncResult

from core.events import WalkoffEvent
from core.helpers import convert_action_argument, create_sse_event
from server.security import jwt_required_in_query

workflowresults_page = Blueprint('workflowresults_page', __name__)

__workflow_shutdown_event_json = AsyncResult()
__workflow_action_event_json = AsyncResult()
__sync_signal = Event()
__action_signal = Event()

__action_event_id_counter = 0
__workflow_event_id_counter = 0


def __workflow_shutdown_event_stream():
    global __workflow_event_id_counter
    while True:
        data = __workflow_shutdown_event_json.get()
        yield create_sse_event(event_id=__workflow_event_id_counter, event='workflow_shutdown', data=data)
        __workflow_event_id_counter += 1
        __sync_signal.wait()


def __workflow_actions_event_stream():
    global __action_event_id_counter
    while True:
        event_type, data = __workflow_action_event_json.get()
        yield create_sse_event(event_id=__action_event_id_counter, event=event_type, data=data)
        __action_event_id_counter += 1
        __action_signal.wait()


@WalkoffEvent.WorkflowShutdown.connect
def __workflow_ended_callback(sender, **kwargs):
    data = 'None'
    if 'data' in kwargs:
        data = kwargs['data']
        if not isinstance(data, str):
            data = str(data)
    result = {'name': sender['name'],
              'timestamp': str(datetime.utcnow()),
              'result': data}
    __workflow_shutdown_event_json.set(result)
    sleep(0)
    __sync_signal.set()
    __sync_signal.clear()
    sleep(0)


@WalkoffEvent.ActionExecutionSuccess.connect
def __action_ended_callback(sender, **kwargs):
    action_arguments = [convert_action_argument(argument) for argument in sender.get('arguments', [])]
    result = {'action_name': sender['name'],
              'action_uid': sender['uid'],
              'timestamp': str(datetime.utcnow()),
              'arguments': action_arguments,
              'result': kwargs['data']['result'],
              'status': kwargs['data']['status']}
    __workflow_action_event_json.set(('action_success', result))
    sleep(0)
    __action_signal.set()
    __action_signal.clear()
    sleep(0)


@WalkoffEvent.ActionExecutionError.connect
def __action_error_callback(sender, **kwargs):
    action_arguments = [convert_action_argument(argument) for argument in sender.get('arguments', [])]
    result = {'action_name': sender['name'],
              'action_uid': sender['uid'],
              'timestamp': str(datetime.utcnow()),
              'arguments': action_arguments,
              'result': kwargs['data']['result'],
              'status': kwargs['data']['status']}
    __workflow_action_event_json.set(('action_error', result))
    sleep(0)
    __action_signal.set()
    __action_signal.clear()
    sleep(0)


@workflowresults_page.route('/stream', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_success_events():
    return Response(__workflow_shutdown_event_stream(), mimetype='text/event-stream')


@workflowresults_page.route('/stream-actions', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_action_events():
    return Response(__workflow_actions_event_stream(), mimetype='text/event-stream')
