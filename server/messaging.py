from server.database import db
from sqlalchemy import func
from datetime import datetime
from core.events import WalkoffEvent


user_messages_association = db.Table('user_messages',
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                                  db.Column('message_id', db.Integer, db.ForeignKey('message.id')))


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message = db.Column(db.String(), nullable=False)
    users = db.relationship('User', secondary=user_messages_association,
                            backref=db.backref('messages', lazy='dynamic'))
    workflow_execution_uid = db.Column(db.String(25))
    requires_reauth = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.current_timestamp())
    read_at = db.Column(db.DateTime)

    def __init__(self, message, workflow_execution_uid, users, requires_reauth=False):
        self.message = message
        self.workflow_execution_uid = workflow_execution_uid
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
        if workflow_execution_uid in self._cache:
            self._cache[workflow_execution_uid] = WorkflowAuthorization(users=users, roles=roles)
        else:
            self._cache[workflow_execution_uid] += WorkflowAuthorization(users=users, roles=roles)

    def is_authorized(self, workflow_execution_uid, user, role):
        return self._cache[workflow_execution_uid].is_authorized(user, role)

    def remove_authorizations(self, workflow_execution_uid):
        self._cache.pop(workflow_execution_uid, None)


_workflow_authorization_cache = WorkflowAuthorizationCache()


@WalkoffEvent.SendMessage.connect
def save_message(sender, **message_data):
    message = message_data['message']
    if any(message_component['requires_auth'] for message_component in message):
        _workflow_authorization_cache.add_authorized_users(
            sender.workflow_execution_uid, users=message_data['users'], roles=message_data['roles'])

    # TODO: find all matching users and users for roles and add to message
    message_entry = Message(message, sender.workflow_execution_uid, requires_reauth=message_data['requires_reauth'])
    db.session.add(message_entry)
    db.session.commit()


