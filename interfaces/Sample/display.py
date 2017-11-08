import time
import random
from flask import Blueprint, Response
from interfaces import AppBlueprint
from threading import Thread
from gevent.event import Event, AsyncResult
from gevent import sleep


blueprint = AppBlueprint(blueprint=Blueprint('HelloWorldPage', __name__))
blueprint2 = AppBlueprint(blueprint=Blueprint('HelloWorldPage2', __name__), rule='/<string:action>')


__sync_signal = Event()
random_event_result = AsyncResult()

def load(*args, **kwargs):
    return {}


# These blueprints will be registered with the Flask app and can be used to make your own endpoints.
@blueprint.blueprint.route('/test_blueprint')
def test_basic_blueprint():
    # This can be called using the url /apps/HelloWorld/test_blueprint
    return 'successfully called basic blueprint'


def random_number_receiver():
    while True:
        data = random_event_result.get()
        yield 'data: %s\n\n' % data
        __sync_signal.wait()


def random_number_pusher():
    while True:
        sleep(2)
        random_event_result.set(random.random())
        __sync_signal.set()
        __sync_signal.clear()


@blueprint.blueprint.route('/stream/random-number')
def stream_random_numbers():
    """
    Example of using coroutines to create an event-driven stream
    :return:
    """
    thread = Thread(target=random_number_pusher)
    thread.start()
    return Response(random_number_receiver(), mimetype='text/event-stream')


@blueprint.blueprint.route('/stream/counter')
def stream_counter():
    """
    Example of using an infinite generator to create a stream
    :return:
    """
    def counter():
        count = 0
        while True:
            time.sleep(1)
            yield 'data: %s\n\n' % count
            count += 1
    return Response(counter(), mimetype='text/event-stream')


@blueprint2.blueprint.route('/test_action_blueprint')
def test_templated_blueprint(action):
    # This url is used by an blueprint2, and can be called using the url /apps/HelloWorld/<action>/test_action_blueprint
    return 'successfully called templated blueprint with action {0}'.format(action)

