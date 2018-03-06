import random

from flask import Blueprint
from gevent import sleep
from gevent import spawn
from gevent.event import Event, AsyncResult

from interfaces import AppBlueprint
from walkoff.sse import InterfaceSseStream

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


counter_stream = InterfaceSseStream('Sample', 'counter')
random_stream = InterfaceSseStream('Sample', 'random')


def random_number_pusher():
    while True:
        sleep(2)
        random_stream.publish(random.random())


@blueprint.blueprint.route('/stream/random-number')
def stream_random_numbers():
    """
    Example of using coroutines to create an event-driven stream
    :return:
    """
    thread = spawn(random_number_pusher)
    thread.start()
    return random_stream.stream()


def counter_pusher():
    count = 0
    while True:
        sleep(1)
        counter_stream.publish(count)
        count += 1


@blueprint.blueprint.route('/stream/counter')
def stream_counter():
    """
    Example of using an infinite generator to create a stream
    :return:
    """
    counter = spawn(counter_pusher)
    counter.spawn()
    return counter_stream.stream()


@blueprint2.blueprint.route('/test_action_blueprint')
def test_templated_blueprint(action):
    # This url is used by an blueprint2, and can be called using the url /apps/HelloWorld/<action>/test_action_blueprint
    return 'successfully called templated blueprint with action {0}'.format(action)
