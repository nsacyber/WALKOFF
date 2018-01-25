from datetime import datetime

from flask import Blueprint
from flask_jwt_extended import get_jwt_identity
from enum import Enum, unique
from walkoff.security import jwt_required_in_query
from walkoff.messaging import MessageActionEvent
from walkoff.sse import SimpleFilteredSseStream

notifications_page = Blueprint('notifications_page', __name__)


@unique
class NotificationSseEvent(Enum):
    created = 1
    read = 2
    responded = 3


sse_stream = SimpleFilteredSseStream('notifications')


@MessageActionEvent.created.connect
@sse_stream.push(NotificationSseEvent.created.name)
def message_created_callback(message, **data):
    result = {'id': message.id,
              'subject': message.subject,
              'created_at': str(message.created_at),
              'is_read': False,
              'awaiting_response': message.requires_response}
    return result, {user.id for user in message.users}


def format_read_responded_data(message, data):
    user = data['data']['user']
    return {'id': message.id,
            'username': user.username,
            'timestamp': str(datetime.utcnow())}


@MessageActionEvent.responded.connect
@sse_stream.push(NotificationSseEvent.responded.name)
def message_responded_callback(message, **data):
    return format_read_responded_data(message, data), {user.id for user in message.users}


@MessageActionEvent.read.connect
@sse_stream.push(NotificationSseEvent.read.name)
def message_read_callback(message, **data):
    return format_read_responded_data(message, data), {user.id for user in message.users}


@notifications_page.route('/stream', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_notifications():
    user_id = get_jwt_identity()
    return sse_stream.stream(subchannel=user_id)
