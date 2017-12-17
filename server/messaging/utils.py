import json
import logging

from core.events import WalkoffEvent
from server.database import Message, Role, User
from server.extensions import db
import server.messaging

logger = logging.getLogger(__name__)


@WalkoffEvent.SendMessage.connect
def save_message_callback(sender, **message_data):
    from server import app

    message_data = message_data['data']
    body = message_data['body']
    requires_action = strip_requires_auth_from_message_body(body)
    if requires_action:
        server.messaging.workflow_authorization_cache.add_authorized_users(
            sender['workflow_execution_uid'], users=message_data['users'], roles=message_data['roles'])
    with app.app_context():
        save_message(body, message_data, sender['workflow_execution_uid'], requires_action)


def strip_requires_auth_from_message_body(body):
    is_caching_required = any(message_component.get('requires_auth', False) for message_component in body['body'])
    for message_component in body['body']:
        message_component.pop('requires_auth', None)
    return is_caching_required


def save_message(body, message_data, workflow_execution_uid, requires_action):
    users = get_all_matching_users_for_message(message_data['users'], message_data['roles'])
    if users:
        subject = message_data.get('subject', '')
        message_entry = Message(
            subject, json.dumps(body['body']), workflow_execution_uid, users, requires_reauth=message_data['requires_reauth'],
            requires_action=requires_action)
        db.session.add(message_entry)
        db.session.commit()
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


@WalkoffEvent.TriggerActionNotTaken.connect
def pop_user_attempt_from_cache(sender, **data):
    workflow_execution_uid = sender['workflow_execution_uid']
    if server.messaging.workflow_authorization_cache.workflow_requires_authorization(workflow_execution_uid):
        server.messaging.workflow_authorization_cache.pop_last_user_in_progress(workflow_execution_uid)


@WalkoffEvent.TriggerActionTaken.connect
def remove_from_cache_and_log(sender, **data):
    workflow_execution_uid = sender['workflow_execution_uid']
    if server.messaging.workflow_authorization_cache.workflow_requires_authorization(workflow_execution_uid):
        from server import app
        with app.app_context():
            user_id = server.messaging.workflow_authorization_cache.pop_last_user_in_progress(workflow_execution_uid)
            server.messaging.workflow_authorization_cache.remove_authorizations(workflow_execution_uid)
            if user_id is not None:
                log_action_taken_on_message(user_id, workflow_execution_uid)
            else:
                logger.error('Workflow authorization cache invalid for {}. '
                             'No users found in users queue'.format(workflow_execution_uid))


def log_action_taken_on_message(user_id, workflow_execution_uid):
    message = Message.query.filter(Message.workflow_execution_uid == workflow_execution_uid).first()
    user = User.query.filter(User.id == user_id).first()
    if user is not None:
        message.record_user_action(user, server.messaging.MessageAction.respond)
        db.session.commit()
    else:
        logger.error('User became invalid between triggering workflow resume and logging message')
