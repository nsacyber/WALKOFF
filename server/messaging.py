from server.database import db
from sqlalchemy import func
from datetime import datetime
from core.events import WalkoffEvent
import json
import logging

logger = logging.getLogger(__name__)

user_messages_association = db.Table('user_messages',
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                                  db.Column('message_id', db.Integer, db.ForeignKey('message.id')))


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject = db.Column(db.String())
    body = db.Column(db.String(), nullable=False)
    users = db.relationship('User', secondary=user_messages_association,
                            backref=db.backref('messages', lazy='dynamic'))
    workflow_execution_uid = db.Column(db.String(25))
    requires_reauth = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.current_timestamp())
    read_at = db.Column(db.DateTime)

    def __init__(self, subject, body, workflow_execution_uid, users, requires_reauth=False):
        self.subject = subject
        self.body = body
        self.workflow_execution_uid = workflow_execution_uid
        self.users = users
        self.requires_reauth = requires_reauth

    def read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()

    def unread(self):
        self.is_read = False
        self.read_at = None

    def as_json(self):
        ret = {'id': self.id,
               'subject': self.subject,
               'body': json.loads(self.body),
               'workflow_execution_uid': self.workflow_execution_uid,
               'requires_reauthorization': self.requires_reauth,
               'is_read': self.is_read,
               'created_at': str(self.created_at)}
        if self.is_read:
            ret['read_at'] = str(self.read_at)
        return ret


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
    is_caching_required = strip_requires_auth_from_message_body(body)
    if is_caching_required:
        workflow_authorization_cache.add_authorized_users(
            sender['workflow_execution_uid'], users=message_data['users'], roles=message_data['roles'])
    save_message(body, message_data, sender['workflow_execution_uid'])


def strip_requires_auth_from_message_body(body):
    is_caching_required = any(message_component.get('requires_auth', False) for message_component in body)
    for message_component in body:
        message_component.pop('requires_auth', None)
    return is_caching_required


def save_message(body, message_data, workflow_execution_uid):
    users = get_all_matching_users_for_message(message_data['users'], message_data['roles'])
    if users:
        subject = message_data.get('subject', '')
        message_entry = Message(
            subject, json.dumps(body), workflow_execution_uid, users, requires_reauth=message_data['requires_reauth'])
        db.session.add(message_entry)
        db.session.commit()
    else:
        logger.error('Cannot send message. Users {0} or roles {1} do not exist'.format(
            message_data['users'], message_data['roles']))


def get_all_matching_users_for_message(user_ids, role_ids):
    from server.context import running_context

    user_id_set = set()
    if role_ids:
        roles = running_context.Role.query.filter(running_context.Role.id.in_(role_ids)).all()
        for role in roles:
            user_id_set |= {user.id for user in role.users}
    user_id_search = set(user_ids) | user_id_set
    if user_id_search:
        return running_context.User.query.filter(running_context.User.id.in_(user_id_search)).all()
    else:
        return []
