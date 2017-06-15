import json
from flask import Blueprint, Response
from gevent.event import Event, AsyncResult
from gevent import sleep
from core.case.callbacks import WorkflowShutdown, FunctionExecutionSuccess, StepExecutionError, StepInputInvalid
from datetime import datetime

workflowresults_page = Blueprint('workflowresults_page', __name__)

__workflow_shutdown_event_json = AsyncResult()
__workflow_step_event_json = AsyncResult()
__sync_signal = Event()
__step_signal = Event()


def __workflow_shutdown_event_stream():
    while True:
        data = __workflow_shutdown_event_json.get()
        yield 'data: %s\n\n' % data
        __sync_signal.wait()


def __workflow_steps_event_stream():
    while True:
        data = __workflow_step_event_json.get()
        yield 'data: %s\n\n' % data
        __step_signal.wait()


def __workflow_ended_callback(sender, **kwargs):
    data = 'None'
    if 'data' in kwargs:
        data = kwargs['data']
        if not isinstance(data, str):
            data = str(data)
    result = {'name': sender.name,
              'timestamp': str(datetime.utcnow()),
              'result': data}
    __workflow_shutdown_event_json.set(json.dumps(result))
    __sync_signal.set()
    __sync_signal.clear()


def __step_ended_callback(sender, **kwargs):
    data = 'None'
    input = str(sender.input)
    if 'data' in kwargs:
        data = kwargs['data']
        if not isinstance(data, str):
            data = str(data)
    result = {'name': sender.name,
              'type': "SUCCESS",
              'input': input,
              'result': data}
    __workflow_step_event_json.set(json.dumps(result))
    __step_signal.set()
    __step_signal.clear()
    sleep(0)


def __step_error_callback(sender, **kwargs):
    data = 'None'
    input = str(sender.input)
    if 'data' in kwargs:
        data = kwargs['data']
        if not isinstance(data, str):
            data = str(data)
    result = {'name': sender.name,
              'type': "ERROR",
              'input': input,
              'result': data}
    __workflow_step_event_json.set(json.dumps(result))
    __step_signal.set()
    __step_signal.clear()
    sleep(0)

WorkflowShutdown.connect(__workflow_ended_callback)

FunctionExecutionSuccess.connect(__step_ended_callback)
StepExecutionError.connect(__step_error_callback)


@workflowresults_page.route('/stream', methods=['GET'])
def stream_workflow_success_events():
    return Response(__workflow_shutdown_event_stream(), mimetype='text/event-stream')


@workflowresults_page.route('/stream-steps', methods=['GET'])
def stream_workflow_step_events():
    return Response(__workflow_steps_event_stream(), mimetype='text/event-stream')