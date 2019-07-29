import json
import logging

from api_gateway.extensions import db


class Bucket(db.Model):
    __tablename__ = 'bucket'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    triggers = db.relationship('BucketTrigger', backref=db.backref('bucket'), cascade='all, delete-orphan')

    def __init__(self, name, description='', triggers=None):
        self.name = name
        self.description = description
        if triggers is not None:
            for t in set(triggers):
                self.triggers.append(BucketTrigger(**t))

    def _get_triggers_as_list(self):
        out = [t.as_json() for t in self.triggers]
        return out

    def as_json(self):
        out = {"name": self.name,
               "description": self.description,
               "triggers": self._get_triggers_as_list()
               }
        return out


class BucketTrigger(db.Model):
    __tablename__ = 'bucket_triggers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bucket_id = db.Column(db.Integer, db.ForeignKey('bucket.id'))
    workflow_id = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.Enum('s3:ObjectCreated:*',
                                   's3:ObjectRemoved:*',
                                   's3:ObjectAccessed:*',
                                   'unspecified', name='event_types'))
    prefix = db.Column(db.String(255), nullable=False)
    suffix = db.Column(db.String(255), nullable=False)


    def __init__(self, workflow_id='', event_type='unspecified', prefix='', suffix=''):
        self.workflow_id = workflow_id
        self.event_type = event_type
        self.prefix = prefix
        self.suffix = suffix

    def as_json(self):
        out = { "workflow_id": self.workflow_id,
                "event_type": self.event_type,
                "prefix": self.prefix,
                "suffix": self.suffix
              }
        return out