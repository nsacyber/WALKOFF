from datetime import datetime

from flask import jsonify
from flask_jwt_extended import jwt_required

from interfaces import dispatcher, AppBlueprint
from walkoff.events import WalkoffEvent
from walkoff.security import jwt_required_in_query
from walkoff.sse import InterfaceSseStream, create_interface_channel_name

blueprint = AppBlueprint('HelloWorldPage__', __name__)


metrics_stream = InterfaceSseStream('HelloWorld', 'metrics')

hello_world_channel_names = {}


def retrieve_actions():
    return {action: blueprint.cache.get(channel_name) for action, channel_name in hello_world_channel_names.items()}


@dispatcher.on_app_actions('HelloWorld', events=WalkoffEvent.ActionStarted, weak=False)
def handle_action_start(data):
    action_name = data['action_name']
    if action_name not in hello_world_channel_names:
        hello_world_channel_names[action_name] = \
            create_interface_channel_name('HelloWorld', 'action_{}'.format(action_name))

    blueprint.cache.incr(hello_world_channel_names[action_name])


@blueprint.route('/metrics', methods=['GET'])
@jwt_required
def get_hello_world_metrics():
    return jsonify(retrieve_actions()), 200


def format_action_data(data):
    data['timestamp'] = str(datetime.utcnow())
    return data


@dispatcher.on_app_actions('HelloWorld', events=WalkoffEvent.ActionExecutionSuccess)
@metrics_stream.push('action_success')
def action_ended_callback(data):
    return format_action_data(data)


@dispatcher.on_app_actions('HelloWorld', events=WalkoffEvent.ActionExecutionError)
@metrics_stream.push('action_error')
def __action_error_callback(data):
    return format_action_data(data)


@blueprint.route('/actionstream', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_action_events():
    return metrics_stream.stream()
