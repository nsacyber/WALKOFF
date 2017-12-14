from server.security import ResourcePermissions, permissions_accepted_for_resources
from flask_jwt_extended import jwt_required, get_jwt_identity
from server.returncodes import *
from flask import request
from server.database import User
from server.extensions import db


def get_all_messages():

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('messages', ['read']))
    def __func():
        user_id = get_jwt_identity()
        user = User.query.filter(User.id == user_id).first()
        return [message.as_json(user=user) for message in user.messages]

    return __func()


def act_on_messages(action):
    from server.messaging import MessageActions

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('messages', ['update']))
    def other_action_func(action):
        return act_on_message_helper(action)

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('messages', ['delete']))
    def delete_message_action():
        return act_on_message_helper(MessageActions.delete)

    action = MessageActions.convert_string(action)
    if action is None:
        return {'error': 'Unknown action: {0}. Possible actions are {1}'.format(
            action, list(MessageActions.get_all_action_names()))}, OBJECT_DNE_ERROR

    if action == MessageActions.delete:
        return delete_message_action()
    else:
        return other_action_func(action)


def act_on_message_helper(action):

    user_id = get_jwt_identity()
    user = User.query.filter(User.id == user_id).first()
    if user is None:
        return {'error': 'Unknown user'}, OBJECT_DNE_ERROR
    for message in (message for message in user.messages if message.id in request.get_json()['ids']):
        message.record_user_action(user, action)
    db.session.commit()
    return 'Success', SUCCESS




