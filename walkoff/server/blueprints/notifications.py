from datetime import datetime

from enum import Enum, unique
from flask_jwt_extended import get_jwt_identity

from walkoff.messaging import MessageActionEvent
from walkoff.security import jwt_required_in_query
from walkoff.sse import FilteredSseStream, StreamableBlueprint

sse_stream = FilteredSseStream('notifications')

notifications_page = StreamableBlueprint('notifications_page', __name__, streams=[sse_stream])


@unique
class NotificationSseEvent(Enum):
    created = 1
    read = 2
    responded = 3


def format_read_responded_data(message, user):
    return {'id': message.id,
            'username': user.username,
            'timestamp': datetime.utcnow().isoformat()}


@MessageActionEvent.created.connect
@sse_stream.push(NotificationSseEvent.created.name)
def message_created_callback(message, **data):
    result = {'id': message.id,
              'subject': message.subject,
              'created_at': message.created_at.isoformat(),
              'is_read': False,
              'awaiting_response': message.requires_response}
    return result, {user.id for user in message.users}


@MessageActionEvent.responded.connect
@sse_stream.push(NotificationSseEvent.responded.name)
def message_responded_callback(message, **data):
    user = data['data']['user']
    result = format_read_responded_data(message, user)
    return result, {user.id for user in message.users}


@MessageActionEvent.read.connect
@sse_stream.push(NotificationSseEvent.read.name)
def message_read_callback(message, **data):
    user = data['data']['user']
    result = format_read_responded_data(message, user)
    return result, {user.id for user in message.users}


@notifications_page.route('/notifications', methods=['GET'])
@jwt_required_in_query('access_token')
def stream_workflow_success_events():
    user_id = get_jwt_identity()
    return sse_stream.stream(subchannel=user_id)
