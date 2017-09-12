import json
from flask import Blueprint, Response
from server.security import roles_accepted
from flask_jwt_extended import jwt_required
from gevent.event import Event, AsyncResult
from gevent import sleep, Timeout

events_page = Blueprint('events_page', __name__)

__case_event_json = AsyncResult()
__sync_signal = Event()


def __case_event_generator():
    while True:
        try:
            data = __case_event_json.get(timeout=60)
            yield 'data: %s\n\n' % data
            __sync_signal.wait()
        except Timeout:
            pass


def __push_to_case_stream(sender, **kwargs):
    out = {'name': sender.name,
           'uid': sender.uid}
    if 'data' in kwargs:
        out['data'] = kwargs['data']
    __case_event_json.set(json.dumps(out))
    sleep(0)
    __sync_signal.set()
    __sync_signal.clear()


def setup_case_stream():
    from blinker import NamedSignal
    import core.case.callbacks as callbacks
    signals = [getattr(callbacks, field) for field in dir(callbacks) if (not field.startswith('__')
                                                                             and isinstance(getattr(callbacks, field),
                                                                                            NamedSignal))]
    for signal in signals:
        signal.connect(__push_to_case_stream)
    pass


@events_page.route('/', methods=['GET'])
@jwt_required
def stream_case_events():
    from server.flaskserver import running_context

    @roles_accepted(*running_context.resource_roles['/cases'])
    def inner():
        return Response(__case_event_generator(), mimetype='text/event-stream')
    return inner()

