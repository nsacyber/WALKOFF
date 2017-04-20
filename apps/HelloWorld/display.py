import gevent
import random
from flask import Blueprint, Response
from server.blueprints import AppBlueprint
from gevent.event import AsyncResult, Event


blueprint = AppBlueprint(blueprint=Blueprint('HelloWorldPage', __name__))
blueprint2 = AppBlueprint(blueprint=Blueprint('HelloWorldPage2', __name__), rule='/<string:action>')


def load(*args, **kwargs):
    return {}


def stream_generator(stream_name):
    def counter():
        count = 0
        while True:
            gevent.sleep(1)
            yield 'data: %s\n\n' % count
            count += 1

    if stream_name == 'counter':
        return counter, 'text/event-stream'
    else:
        return None, None


# These blueprints will be registered with the Flask app and can be used to make your own endpoints.
@blueprint.blueprint.route('/test_blueprint')
def test_basic_blueprint():
    # This can be called using the url /apps/HelloWorld/test_blueprint
    return 'successfully called basic blueprint'


__random_num_event = AsyncResult()
__sync = Event()


def rand_co():
    while True:
        data = __random_num_event.get()
        yield 'data: %s\n\n' % data
        __sync.wait()


def pusher():
    while True:
        __random_num_event.set(random.random())
        gevent.sleep(2)
        __sync.set()
        __sync.clear()


@blueprint.blueprint.route('/stream/random-number')
def stream_random_numbers():
    """
    Example of using gevent and AsyncResults to create an event-driven stream
    :return:
    """
    gevent.spawn(pusher)
    return Response(rand_co(), mimetype='text/event-stream')


@blueprint.blueprint.route('/stream/counter')
def stream_counter():
    """
    Example of using an infinite generator to create a stream
    :return:
    """
    def counter():
        count = 0
        while True:
            gevent.sleep(1)
            yield 'data: %s\n\n' % count
            count += 1
    return Response(counter(), mimetype='text/event-stream')


@blueprint2.blueprint.route('/test_action_blueprint')
def test_templated_blueprint(action):
    # This url is used by an blueprint2, and can be called using the url /apps/HelloWorld/<action>/test_action_blueprint
    return 'successfully called templated blueprint with action {0}'.format(action)

