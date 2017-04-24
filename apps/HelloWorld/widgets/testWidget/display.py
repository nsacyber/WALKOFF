import gevent
from gevent.event import Event, AsyncResult
import random
from flask import Blueprint, Response
from server.blueprints import WidgetBlueprint

blueprint = WidgetBlueprint(blueprint=Blueprint('HelloWorldTestWidgetPage', __name__))
blueprint2 = WidgetBlueprint(blueprint=Blueprint('HelloWorldTestWidgetPage2', __name__), rule='/<string:action>')


def load(*args, **kwargs):
    return {}


# These blueprints will be registered with the Flask app and can be used to make your own endpoints.
@blueprint.blueprint.route('/test_blueprint')
def test_basic_blueprint():
    # This can be called using the url /apps/HelloWorld/testWidget/test_blueprint
    return 'successfully called basic blueprint'

__random_num_event = AsyncResult()
__sync = Event()


def random_number_receiver():
    while True:
        data = __random_num_event.get()
        yield 'data: %s\n\n' % data
        __sync.wait()


def random_number_pusher():
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
    gevent.spawn(random_number_pusher)
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
            gevent.sleep(1)
            yield 'data: %s\n\n' % count
            count += 1
    return Response(counter(), mimetype='text/event-stream')


@blueprint2.blueprint.route('/test_action_blueprint')
def test_templated_blueprint(action):
    # This url is used by an blueprint2,
    # and can be called using the url /apps/HelloWorld/testWidget/<action>/test_action_blueprint
    return 'successfully called templated blueprint with action {0}'.format(action)

