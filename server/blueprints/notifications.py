from datetime import datetime

from flask import Blueprint, Response
from flask_jwt_extended import get_jwt_identity
from gevent import sleep
from gevent.event import Event, AsyncResult
from enum import Enum, unique
from core.helpers import create_sse_event
from server.security import jwt_required_in_query
from server.messaging import MessageActionEvent

notifications_page = Blueprint('notifications_page', __name__)

notification_event_result = AsyncResult()
sync_signal = Event()


@unique
class NotificationSseEvent(Enum):
    created = 1
    read = 2
    responded = 3


def notification_event_stream(user_id):
    sync_signal.wait()
    event_id = 1
    while True:
        user_ids, event, data = notification_event_result.get()
        if user_id in user_ids:
            yield create_sse_event(event_id=event_id, event=event.name, data=data)
            event_id += 1
        sync_signal.wait()


def send_sse(user_id, event, data):
    notification_event_result.set((user_id, event, data))
    sleep(0)
    sync_signal.set()
    sync_signal.clear()
    sleep(0)


@MessageActionEvent.created.connect
def message_created_callback(message, **data):
    result = {'id': message.id,
              'subject': message.subject,
              'created_at': str(message.created_at),
              'is_read': False,
              'awaiting_response': message.requires_response}
    send_sse({user.id for user in message.users}, NotificationSseEvent.created, result)


@MessageActionEvent.responded.connect
def message_responded_callback(message, **data):
    user = data['data']['user']
    result = {'id': message.id,
              'username': user.username,
              'timestamp': str(datetime.utcnow())}
    send_sse({user.id for user in message.users}, NotificationSseEvent.responded, result)


@MessageActionEvent.read.connect
def message_read_callback(message, **data):
    user = data['data']['user']
    result = {'id': message.id,
              'username': user.username,
              'timestamp': str(datetime.utcnow())}
    send_sse({user.id for user in message.users}, NotificationSseEvent.read, result)


@notifications_page.route('/stream', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_success_events():
    user_id = get_jwt_identity()
    return Response(notification_event_stream(user_id), mimetype='text/event-stream')
