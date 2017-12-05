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

    def __init__(self, message, workflow_execution_uid, requires_reauth=False):
        self.message = message
        self.workflow_execution_uid = workflow_execution_uid
        self.requires_reauth = requires_reauth

    def read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()



@WalkoffEvent.SendMessage.connect
def save_message(message, **data):
    pass


