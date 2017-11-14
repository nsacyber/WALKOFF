from flask import Blueprint, Response
from gevent.event import Event, AsyncResult
from gevent import sleep
from core.case.callbacks import WorkflowShutdown, FunctionExecutionSuccess, StepExecutionError
from datetime import datetime
from server.security import jwt_required_in_query
import server.workflowresults  # do not delete needed to register callbacks

workflowresults_page = Blueprint('workflowresults_page', __name__)

__workflow_shutdown_event_json = AsyncResult()
__workflow_step_event_json = AsyncResult()
__sync_signal = Event()
__step_signal = Event()

__step_event_id_counter = 0
__workflow_event_id_counter = 0


def __workflow_shutdown_event_stream():
    global __workflow_event_id_counter
    while True:
        data = __workflow_shutdown_event_json.get()
        yield 'event: workflow_shutdown\nid: {0}\ndata: {1}\n\n'.format(__workflow_event_id_counter, data)
        __workflow_event_id_counter += 1
        __sync_signal.wait()


def __workflow_steps_event_stream():
    global __step_event_id_counter
    while True:
        event_type, data = __workflow_step_event_json.get()
        yield 'event: {0}\nid: {1}\ndata: {2}\n\n'.format(event_type, __step_event_id_counter, data)
        __step_event_id_counter += 1
        __step_signal.wait()


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


def convert_argument(argument):
    converted_arg = {}
    for field in ('name', 'value', 'reference', 'selector'):
        if hasattr(argument, field):
            attribute = getattr(argument, field)
            if field == 'value':
                converted_arg[field] = attribute
            elif attribute:
                converted_arg[field] = attribute
    return converted_arg


@FunctionExecutionSuccess.connect
def __step_ended_callback(sender, **kwargs):
    data = 'None'
    step_arguments = [convert_argument(argument) for argument in list(sender.arguments)]

    if 'data' in kwargs:
        data = kwargs['data']
    result = {'name': sender.name,
              'timestamp': str(datetime.utcnow()),
              'arguments': step_arguments,
              'result': data}
    __workflow_step_event_json.set(('step_success', result))
    sleep(0)
    __step_signal.set()
    __step_signal.clear()
    sleep(0)


@StepExecutionError.connect
def __step_error_callback(sender, **kwargs):
    result = {'name': sender.name}
    if 'data' in kwargs:
        data = kwargs['data']
        result['arguments'] = data['arguments']
        result['result'] = data['result']
        result['timestamp'] = str(datetime.utcnow())
    __workflow_step_event_json.set(('step_error', result))
    sleep(0)
    __step_signal.set()
    __step_signal.clear()
    sleep(0)


@workflowresults_page.route('/stream', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_success_events():
    return Response(__workflow_shutdown_event_stream(), mimetype='text/event-stream')


@workflowresults_page.route('/stream-steps', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_step_events():
    return Response(__workflow_steps_event_stream(), mimetype='text/event-stream')
