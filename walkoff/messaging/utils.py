import json
import logging

import walkoff.messaging
from walkoff.events import WalkoffEvent
from walkoff.extensions import db
from walkoff.serverdb import Role, User
from walkoff.serverdb.message import Message
from flask import current_app

logger = logging.getLogger(__name__)


@WalkoffEvent.SendMessage.connect
def save_message_callback(sender, **message_data):
    workflow_data = message_data['data']['workflow']
    message_data = message_data['data']['message']
    body = message_data['body']

    requires_action = strip_requires_response_from_message_body(body)
    with current_app.app_context():
        save_message(body, message_data, workflow_data['execution_id'], requires_action)


def strip_requires_response_from_message_body(body):
    is_action_required = any(message_component.get('requires_response', False) for message_component in body)
    for message_component in body:
        message_component.pop('requires_response', None)
    return is_action_required


def save_message(body, message_data, workflow_execution_id, requires_action):
    users = get_all_matching_users_for_message(message_data['users'], message_data['roles'])
    roles = get_all_matching_roles_for_message(message_data['roles'])
    if users:
        subject = message_data.get('subject', '')
        message_entry = Message(
            subject, json.dumps(body), workflow_execution_id, users, roles,
            requires_reauth=message_data['requires_reauth'], requires_response=requires_action)
        db.session.add(message_entry)
        db.session.commit()
        walkoff.messaging.MessageActionEvent.created.send(message_entry)
    else:
        logger.error('Cannot send message. Users {0} or roles {1} do not exist'.format(
            message_data['users'], message_data['roles']))


def get_all_matching_users_for_message(user_ids, role_ids):
    user_id_set = set()
    if role_ids:
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        for role in roles:
            user_id_set |= {user.id for user in role.users}
    user_id_search = set(user_ids) | user_id_set
    if user_id_search:
        return User.query.filter(User.id.in_(user_id_search)).all()
    else:
        return []


def get_all_matching_roles_for_message(role_ids):
    if role_ids:
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        return roles
    return []


def log_action_taken_on_message(user_id, workflow_execution_id):
    message = Message.query.filter(Message.workflow_execution_id == workflow_execution_id).first()
    if message and message.requires_response:
        user = User.query.filter(User.id == user_id).first()
        if user is not None:
            message.record_user_action(user, walkoff.messaging.MessageAction.respond)
            db.session.commit()
            walkoff.messaging.MessageActionEvent.responded.send(message, data={'user': user})
        else:
            logger.error('User became invalid between triggering workflow resume and logging message')
