import json
from datetime import datetime

from flask import Blueprint, Response
from gevent import sleep
from gevent.event import Event, AsyncResult

from core.case.callbacks import WorkflowShutdown, ActionExecutionSuccess, ActionExecutionError
from core.helpers import convert_argument
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
        yield 'event: workflow_shutdown\nid: {0}\ndata: {1}\n\n'.format(__workflow_event_id_counter, json.dumps(data))
        __workflow_event_id_counter += 1
        __sync_signal.wait()


def __workflow_actions_event_stream():
    global __action_event_id_counter
    while True:
        event_type, data = __workflow_action_event_json.get()
        yield 'event: {0}\nid: {1}\ndata: {2}\n\n'.format(event_type, __action_event_id_counter, json.dumps(data))
        __action_event_id_counter += 1
        __action_signal.wait()


@WorkflowShutdown.connect
def __workflow_ended_callback(sender, **kwargs):
    data = 'None'
    if 'data' in kwargs:
        data = kwargs['data']
        if not isinstance(data, str):
            data = str(data)
    result = {'name': sender.name,
              'timestamp': str(datetime.utcnow()),
              'result': data}
    __workflow_shutdown_event_json.set(result)
    __sync_signal.set()
    __sync_signal.clear()


@ActionExecutionSuccess.connect
def __action_ended_callback(sender, **kwargs):
    data = 'None'
    action_arguments = [convert_argument(argument) for argument in list(sender.arguments)]

    if 'data' in kwargs:
        data = kwargs['data']
    result = {'action_name': sender.name,
              'action_uid': sender.uid,
              'timestamp': str(datetime.utcnow()),
              'arguments': action_arguments,
              'result': data['result'],
              'status': data['status']}
    __workflow_action_event_json.set(('action_success', result))
    sleep(0)
    __action_signal.set()
    __action_signal.clear()
    sleep(0)


@ActionExecutionError.connect
def __action_error_callback(sender, **kwargs):
    result = {'action_name': sender.name, 'action_uid': sender.uid}
    if 'data' in kwargs:
        data = kwargs['data']
        result['arguments'] = data['arguments']
        result['result'] = data['result']['result']
        result['status'] = data['result']['status']
        result['timestamp'] = str(datetime.utcnow())
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
