import json
import logging
from datetime import datetime

from sqlalchemy_utils import UUIDType

from walkoff.extensions import db
from walkoff.helpers import utc_as_rfc_datetime
from walkoff.messaging import MessageAction

logger = logging.getLogger(__name__)

user_messages_association = db.Table('user_messages',
                                     db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                                     db.Column('message_id', db.Integer, db.ForeignKey('message.id')))

role_messages_association = db.Table('role_messages',
                                     db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                                     db.Column('message_id', db.Integer, db.ForeignKey('message.id')))


class Message(db.Model):
    """Flask-SqlAlchemy Table which holds messages for users.

    It has a many to many relationship with both the users and roles tables.

    Attributes:
        id (int): The primary key
        subject (str): The subject of the message
        body (str): The body of the message as a JSON string
        users (list[User]): The users to which this message was sent and who haven't deleted the message
        roles (list[Role]): The roles to which this message was sent
        workflow_execution_id (UUID): The execution id of the workflow which sent the message
        requires_reauth (bool): Does the message require reauthentication to address it?
        requires_response (bool): Does the message require a response?
        created_at (datetime): Timestamp of message creation
        history (list[MessageHistory]): The timeline of actions taken on this message

    Args:
        subject (str): The subject of the message
        body (str): The body of the message as a JSON string
        users (list[User]): The users to which this message was sent and who haven't deleted the message
        roles (list[Role]): The roles to which this message was sent
        requires_reauth (bool): Does the message require reauthentication to address it?
        requires_response (bool): Does the message require a response?
    """
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject = db.Column(db.String())
    body = db.Column(db.String(), nullable=False)
    users = db.relationship('User', secondary=user_messages_association, backref=db.backref('messages', lazy='dynamic'))
    roles = db.relationship('Role', secondary=role_messages_association, backref=db.backref('messages', lazy='dynamic'))
    workflow_execution_id = db.Column(UUIDType(binary=False), nullable=False)
    requires_reauth = db.Column(db.Boolean, default=False)
    requires_response = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    history = db.relationship('MessageHistory', backref='message', lazy=True)

    def __init__(self, subject, body, workflow_execution_id, users=None, roles=None, requires_reauth=False,
                 requires_response=False):
        self.subject = subject
        self.body = body
        self.workflow_execution_id = workflow_execution_id
        if not (users or roles):
            message = 'Message must have users and/or roles, but has neither.'
            logger.error(message)
            raise ValueError(message)
        self.users = users if users else []
        self.roles = roles if roles else []
        self.requires_reauth = requires_reauth
        self.requires_response = requires_response

    def record_user_action(self, user, action):
        """Records an action taken by a user on this message

        Args:
            user (User): The user taking the action
            action (MessageAction): The action taken
        """
        if user in self.users:
            if ((action == MessageAction.unread and not self.user_has_read(user))
                    or (action == MessageAction.respond and (not self.requires_response or self.is_responded()[0]))):
                return
            elif action == MessageAction.delete:
                self.users.remove(user)
            self.history.append(MessageHistory(user, action))

    def user_has_read(self, user):
        """Determines if a user has read the message

        Args:
            user (User): The user of the query

        Returns:
            (bool): Has the user read the message?
        """
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
        """Gets the last time the user has read the message

        Args:
            user (User): The user of the query

        Returns:
            (datetime|None): The timestamp of the last time the user has read the message or None if the message has not
                been read by this user
        """
        user_history = [history_entry for history_entry in self.history if history_entry.user_id == user.id]
        for history_entry in user_history[::-1]:
            if history_entry.action == MessageAction.read:
                return history_entry.timestamp
        else:
            return None

    def get_read_by(self):
        """Gets all the usernames of the users who have read this message

        Returns:
            set(str): The usernames of the users who have read this message
        """
        return {entry.username for entry in self.history if entry.action == MessageAction.read}

    def is_responded(self):
        """Has this message been responded to?

        Returns:
            tuple(bool, datetime|None, str|None): A tuple of if the message has been responded to, if it has then the
                datetime of when it was responded to and username of the user who responded to it.
        """
        if not self.requires_response:
            return False, None, None
        for history_entry in self.history[::-1]:
            if history_entry.action == MessageAction.respond:
                return True, history_entry.timestamp, history_entry.username
        else:
            return False, None, None

    def is_authorized(self, user_id=None, role_ids=None):
        """Is a user authorized to respond to this message?

        Args:
            user_id (int): The ID of the user
            role_ids (list[int]): The ids of the roles the user has

        Returns:
            (bool)
        """
        if user_id:
            for user in self.users:
                if user_id == user.id:
                    return True

        if role_ids:
            if isinstance(role_ids, int):
                role_ids = [role_ids]
            for role_id in role_ids:
                for role in self.roles:
                    if role_id == role.id:
                        return True

        return False

    def as_json(self, with_read_by=True, user=None, summary=False):
        """Gets a JSON representation of the message

        Args:
            with_read_by (bool, optional): Should the JSON include who has read the message? Defaults to True.
            user (User, optional): If provided, information specific to the user is included.
            summary (bool, optional): If True, only give a brief summary of the messsage. Defaults to False.

        Returns:

        """
        responded, responded_at, responded_by = self.is_responded()
        ret = {'id': self.id,
               'subject': self.subject,
               'created_at': utc_as_rfc_datetime(self.created_at),
               'awaiting_response': self.requires_response and not responded}

        if user:
            ret['is_read'] = self.user_has_read(user)
            last_read_at = self.user_last_read_at(user)
            if last_read_at:
                ret['last_read_at'] = utc_as_rfc_datetime(last_read_at)
        if not summary:
            ret.update({'body': json.loads(self.body),
                        'workflow_execution_id': str(self.workflow_execution_id),
                        'requires_reauthorization': self.requires_reauth,
                        'requires_response': self.requires_response})
            if responded:
                ret['responded_at'] = utc_as_rfc_datetime(responded_at)
                ret['responded_by'] = responded_by
            if with_read_by:
                ret['read_by'] = list(self.get_read_by())
        return ret


class MessageHistory(db.Model):
    """A Flask-SqlAlchemy table which contains entries related to the history of a message

    Attributes:
        id (int): The primary key
        action (MessageAction): The action taken
        timestamp (datetime): The timestamp of the action
        user_id (int): The ID of the user who took the action
        username (str): The username of the user who took the action

    Args:
        user (User): The user who took the action
        action (MessageAction): The action taken
    """
    __tablename__ = 'message_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action = db.Column(db.Enum(MessageAction, name='message_action'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))

    def __init__(self, user, action):
        self.action = action
        self.user_id = user.id
        self.username = user.username

    def as_json(self):
        """gets a JSON representation of the message history entry

        Returns:
            dict: The JSON representation of the message history entry
        """
        return {'action': self.action.name,
                'user_id': self.user_id,
                'username': self.username,
                'id': self.id,
                'timestamp': utc_as_rfc_datetime(self.timestamp)}
