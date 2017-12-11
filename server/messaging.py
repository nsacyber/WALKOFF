from server.database import db
from sqlalchemy import func
from datetime import datetime
from core.events import WalkoffEvent
from server.context import running_context


user_messages_association = db.Table('user_messages',
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                                  db.Column('message_id', db.Integer, db.ForeignKey('message.id')))


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    body = db.Column(db.String(), nullable=False)
    users = db.relationship('User', secondary=user_messages_association,
                            backref=db.backref('messages', lazy='dynamic'))
    workflow_execution_uid = db.Column(db.String(25))
    requires_reauth = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.current_timestamp())
    read_at = db.Column(db.DateTime)

    def __init__(self, body, workflow_execution_uid, users, requires_reauth=False):
        self.body = body
        self.workflow_execution_uid = workflow_execution_uid
        self.users = users
        self.requires_reauth = requires_reauth

    def read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()


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


_workflow_authorization_cache = WorkflowAuthorizationCache()


@WalkoffEvent.SendMessage.connect
def save_message(sender, **message_data):
    message = message_data['message']
    if any(message_component['requires_auth'] for message_component in message):
        _workflow_authorization_cache.add_authorized_users(
            sender.workflow_execution_uid, users=message_data['users'], roles=message_data['roles'])
    users = get_all_matching_users_for_message(message_data['users'], message_data['roles'])
    message_entry = Message(
        message, sender.workflow_execution_uid, users, requires_reauth=message_data['requires_reauth'])
    db.session.add(message_entry)
    db.session.commit()


def get_all_matching_users_for_message(user_ids, role_ids):
    user_id_set = set()
    if role_ids:
        roles = running_context.Role.query.filter_by(id in role_ids).all()
        for role in roles:
            user_id_set |= {user.id for user in role.users}
    return running_context.User.query.filter_by(id in set(user_ids) | user_id_set).all()
