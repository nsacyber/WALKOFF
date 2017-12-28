from interfaces import dispatcher, AppBlueprint
from walkoff.events import WalkoffEvent
from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required
from gevent import sleep
from gevent.event import AsyncResult, Event
from datetime import datetime
from walkoff.security import jwt_required_in_query
from walkoff.core.helpers import create_sse_event

blueprint = AppBlueprint(blueprint=Blueprint('HelloWorldPage__', __name__))

hello_world_action_count = {}

action_event_json = AsyncResult()
action_signal = Event()

action_event_id_counter = 0


@dispatcher.on_app_actions('HelloWorld', events=WalkoffEvent.ActionStarted, weak=False)
def handle_action_start(data):
    global hello_world_action_count
    action_name = data['action_name']

    if action_name not in hello_world_action_count:
        hello_world_action_count[action_name] = 1
    else:
        hello_world_action_count[action_name] += 1


@blueprint.blueprint.route('/metrics', methods=['GET'])
@jwt_required
def get_hello_world_metrics():
    global hello_world_action_count
    return jsonify(hello_world_action_count), 200


def action_event_stream():
    global action_event_id_counter
    while True:
        event_type, data = action_event_json.get()
        yield create_sse_event(event_id=action_event_id_counter, event=event_type, data=data)
        action_event_id_counter += 1
        action_signal.wait()


@dispatcher.on_app_actions('HelloWorld', events=WalkoffEvent.ActionExecutionSuccess)
def action_ended_callback(data):
    data['timestamp'] = str(datetime.utcnow())
    action_event_json.set(('action_success', data))
    sleep(0)
    action_signal.set()
    action_signal.clear()
    sleep(0)


@dispatcher.on_app_actions('HelloWorld', events=WalkoffEvent.ActionExecutionError)
def __action_error_callback(data):
    data['timestamp'] = str(datetime.utcnow())
    action_event_json.set(('action_success', data))
    sleep(0)
    action_signal.set()
    action_signal.clear()
    sleep(0)


@blueprint.blueprint.route('/actionstream', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_action_events():
    return Response(action_event_stream(), mimetype='text/event-stream')
