import json
from flask import Blueprint, Response
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context
from gevent.event import Event, AsyncResult
from core.case.callbacks import WorkflowShutdown
from datetime import datetime

workflowresults_page = Blueprint('workflowresults_page', __name__)

__workflow_shutdown_event_json = AsyncResult()
__sync_signal = Event()


def __workflow_shutdown_event_stream():
    while True:
        data = __workflow_shutdown_event_json.get()
        yield 'data: %s\n\n' % data
        __sync_signal.wait()


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


WorkflowShutdown.connect(__workflow_ended_callback)


@workflowresults_page.route('/stream', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbooks'])
def stream_workflow_success_events():
    return Response(__workflow_shutdown_event_stream(), mimetype='text/event-stream')
