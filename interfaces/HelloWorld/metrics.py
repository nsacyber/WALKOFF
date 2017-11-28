from interfaces import dispatcher, AppBlueprint
from core.events import WalkoffEvent
from flask import Blueprint, jsonify

blueprint = AppBlueprint(blueprint=Blueprint('HelloWorldPage__', __name__))

hello_world_action_count = {}


@dispatcher.on_app_actions('HelloWorld', events=WalkoffEvent.ActionStarted, weak=False)
def handle_action_start(data):
    global hello_world_action_count
    action_name = data['action_name']

    if action_name not in hello_world_action_count:
        hello_world_action_count[action_name] = 1
    else:
        hello_world_action_count[action_name] += 1


@blueprint.blueprint.route('/metrics', methods=['GET'])
def get_hello_world_metrics():
    global hello_world_action_count
    return jsonify(hello_world_action_count), 200

