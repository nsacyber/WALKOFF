import gevent
import random
from flask import Blueprint
from server.blueprints import AppBlueprint

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

    def random_number():
        while True:
            gevent.sleep(1)
            yield 'data: %s\n\n' % random.random()

    if stream_name == 'counter':
        return counter, 'text/event-stream'
    elif stream_name == 'random-number':
        return random_number, 'text/event-stream'
    else:
        return None, None


# These blueprints will be registered with the Flask app and can be used to make your own endpoints.
@blueprint.blueprint.route('/test_blueprint')
def test_basic_blueprint():
    # This can be called using the url /apps/HelloWorld/test_blueprint
    return 'successfully called basic blueprint'


@blueprint2.blueprint.route('/test_action_blueprint')
def test_templated_blueprint(action):
    # This url is used by an blueprint2, and can be called using the url /apps/HelloWorld/<action>/test_action_blueprint
    return 'successfully called templated blueprint with action {0}'.format(action)
