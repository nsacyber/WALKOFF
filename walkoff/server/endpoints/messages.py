from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from walkoff.extensions import db
from walkoff.security import ResourcePermissions, permissions_accepted_for_resources
from walkoff.server.problem import Problem
from walkoff.server.returncodes import *
from walkoff.serverdb import User
from walkoff.serverdb.message import Message

max_notifications = 20
min_notifications = 5


def get_all_messages():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('messages', ['read']))
    def __func():
        user_id = get_jwt_identity()
        user = User.query.filter(User.id == user_id).first()

        page = request.args.get('page', 1, type=int)
        messages = user.messages[(page-1)*current_app['ITEMS_PER_PAGE']: page*current_app['ITEMS_PER_PAGE']]
        return [message.as_json(user=user, summary=True) for message in messages]

    return __func()


def get_message(message_id):
    from walkoff.messaging import MessageActionEvent, MessageAction

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('messages', ['read']))
    def __func():
        user_id = get_jwt_identity()
        user = User.query.filter(User.id == user_id).first()
        message = Message.query.filter(Message.id == message_id).first()
        if message is None:
            return Problem(OBJECT_DNE_ERROR, 'Cannot read message.', 'Message {} does not exist.'.format(message_id))
        if user not in message.users:
            return Problem(
                FORBIDDEN_ERROR,
                'message',
                'read',
                'User is not allowed to access message {}'.format(message_id))
        message.record_user_action(user, MessageAction.read)
        db.session.commit()
        MessageActionEvent.read.send(message, data={'user': user})
        return message.as_json(user=user), SUCCESS

    return __func()


def act_on_messages():
    from walkoff.messaging import MessageAction

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('messages', ['update']))
    def other_action_func(action_):
        return act_on_message_helper(action_)

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('messages', ['delete']))
    def delete_message_action():
        return act_on_message_helper(MessageAction.delete)

    action = MessageAction.convert_string(request.get_json()['action'])
    if action is None or action == MessageAction.respond:
        possible_actions = [action.name for action in MessageAction if action != MessageAction.respond]
        return Problem(
            OBJECT_DNE_ERROR,
            'Unknown action on messages.',
            'Unknown action: {0}. Possible actions are {1}.'.format(action, possible_actions))

    if action == MessageAction.delete:
        return delete_message_action()
    else:
        return other_action_func(action)


def act_on_message_helper(action):
    from walkoff.messaging import MessageAction, MessageActionEvent

    user_id = get_jwt_identity()
    user = User.query.filter(User.id == user_id).first()
    if user is None:
        return Problem(
            OBJECT_DNE_ERROR,
            'Cannot act on messages.',
            'User {} does not exist, so messages cannot be accessed.'.format(user_id))
    send_read_callback = action == MessageAction.read
    for message in (message for message in user.messages if message.id in request.get_json()['ids']):
        message.record_user_action(user, action)
        if send_read_callback:
            MessageActionEvent.read.send(message, data={'user': user})

    db.session.commit()
    return 'Success', SUCCESS


def get_recent_notifications():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('messages', ['read']))
    def __func():
        user_id = get_jwt_identity()
        user = User.query.filter(User.id == user_id).first()
        # This should probably be replaced by a better SqlAlchemy command!
        unread_messages = []
        read_messages = []
        fill_in_with_read = True
        for message in user.messages:
            if not message.user_has_read(user):
                unread_messages.append(message)
            elif fill_in_with_read:
                if len(unread_messages) > min_notifications:
                    fill_in_with_read = False
                else:
                    read_messages.append(message)
        if fill_in_with_read and len(unread_messages) < min_notifications:
            unread_messages += read_messages
            unread_messages = unread_messages[:5]
        unread_messages.sort(key=(lambda x: x.created_at), reverse=True)
        return [message.as_json(user=user, summary=True) for message in unread_messages[:max_notifications]]

    return __func()
