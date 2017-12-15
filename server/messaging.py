from server.database import db, Role, User
from sqlalchemy import func
from core.events import WalkoffEvent
import json
import logging
from enum import Enum, unique
from server import app

logger = logging.getLogger(__name__)

user_messages_association = db.Table('user_messages',
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                                  db.Column('message_id', db.Integer, db.ForeignKey('message.id')))


@unique
class MessageAction(Enum):
    read = 1
    unread = 2
    delete = 3
    act = 4

    @classmethod
    def get_all_action_names(cls):
        return [action.name for action in cls]

    @classmethod
    def convert_string(cls, name):
        return next((action for action in cls if action.name == name), None)


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject = db.Column(db.String())
    body = db.Column(db.String(), nullable=False)
    users = db.relationship('User', secondary=user_messages_association,
                            backref=db.backref('messages', lazy='dynamic'))
    workflow_execution_uid = db.Column(db.String(25))
    requires_reauth = db.Column(db.Boolean, default=False)
    requires_action = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.current_timestamp())
    history = db.relationship('MessageHistory', backref='message', lazy=True)

    def __init__(self, subject, body, workflow_execution_uid, users, requires_reauth=False, requires_action=False):
        self.subject = subject
        self.body = body
        self.workflow_execution_uid = workflow_execution_uid
        self.users = users
        self.requires_reauth = requires_reauth
        self.requires_action = requires_action

    def record_user_action(self, user, action):
        if user in self.users:
            if ((action == MessageAction.unread and not self.user_has_read(user))
                    or (action == MessageAction.act and (not self.requires_action or self.is_acted_on()[0]))):
                return
            elif action == MessageAction.delete:
                self.users.remove(user)
            self.history.append(MessageHistory(user, action))

    def user_has_read(self, user):
        user_history = [history_entry for history_entry in self.history if history_entry.user_id == user.id]
        for history_entry in user_history[::-1]:
            if history_entry.action in (MessageAction.read, MessageAction.unread):
                if history_entry.action == MessageAction.unread:
                    return False
                if history_entry.action == MessageAction.read:
                    return True
        else:
            return False

    def user_last_read_at(self, user):
        user_history = [history_entry for history_entry in self.history if history_entry.user_id == user.id]
        for history_entry in user_history[::-1]:
            if history_entry.action == MessageAction.read:
                return history_entry.timestamp
        else:
            return None

    def get_read_by(self):
        return {entry.username for entry in self.history if entry.action == MessageAction.read}

    def is_acted_on(self):
        if not self.requires_action:
            return False, None, None
        for history_entry in self.history[::-1]:
            if history_entry.action == MessageAction.act:
                return True, history_entry.timestamp, history_entry.username
        else:
            return False, None, None

    def as_json(self, with_read_by=True, user=None):
        is_acted_on, acted_on_timestamp, acted_on_by = self.is_acted_on()
        ret = {'id': self.id,
               'subject': self.subject,
               'body': json.loads(self.body),
               'workflow_execution_uid': self.workflow_execution_uid,
               'requires_reauthorization': self.requires_reauth,
               'requires_action': self.requires_action,
               'created_at': str(self.created_at),
               'awaiting_action': self.requires_action and not is_acted_on}
        if is_acted_on:
            ret['acted_on_at'] = str(acted_on_timestamp)
            ret['acted_on_by'] = acted_on_by
        if with_read_by:
            ret['read_by'] = list(self.get_read_by())
        if user:
            ret['is_read'] = self.user_has_read(user)
            ret['last_read_at'] = str(self.user_last_read_at(user))
        return ret


class MessageHistory(db.Model):
    __tablename__ = 'message_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action = db.Column(db.Enum(MessageAction))
    timestamp = db.Column(db.DateTime, default=func.current_timestamp())
    user_id = db.Column(db.Integer)
    username = db.Column(db.String)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))

    def __init__(self, user, action):
        self.action = action
        self.user_id = user.id
        self.username = user.username

    def as_json(self):
        return {'action': self.action.name,
                'user_id': self.user_id,
                'username': self.username,
                'id': self.id,
                'timestamp': str(self.timestamp)}


class WorkflowAuthorization(object):
    def __init__(self, users=None, roles=None):
        self.users = set(users) if users is not None else set()
        self.roles = set(roles) if roles is not None else set()

    def is_authorized(self, user, role):
        return user in self.users or role in self.roles

    def __add__(self, other):
        users = self.users | other.users
        roles = self.roles | other.roles
        return WorkflowAuthorization(users, roles)


class WorkflowAuthorizationCache(object):

    def __init__(self):
        self._cache = {}

    def add_authorized_users(self, workflow_execution_uid, users=None, roles=None):
        if workflow_execution_uid not in self._cache:
            self._cache[workflow_execution_uid] = WorkflowAuthorization(users=users, roles=roles)
        else:
            self._cache[workflow_execution_uid] += WorkflowAuthorization(users=users, roles=roles)

    def is_authorized(self, workflow_execution_uid, user, role):
        if workflow_execution_uid in self._cache:
            return self._cache[workflow_execution_uid].is_authorized(user, role)
        return False

    def remove_authorizations(self, workflow_execution_uid):
        self._cache.pop(workflow_execution_uid, None)

    def workflow_requires_authorization(self, workflow_execution_uid):
        return workflow_execution_uid in self._cache


workflow_authorization_cache = WorkflowAuthorizationCache()


@WalkoffEvent.SendMessage.connect
def save_message_callback(sender, **message_data):
    message_data = message_data['data']
    body = message_data['body']
    requires_action = strip_requires_auth_from_message_body(body)
    if requires_action:
        workflow_authorization_cache.add_authorized_users(
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
