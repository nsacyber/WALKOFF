import os
from common.config import config, static
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists, InvalidBucketError, NoSuchBucket)

from api_gateway.extensions import db
from sqlalchemy import orm


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

    def create_bucket_in_minio(self, name):
        mc = Minio(config.MINIO, access_key=config.get_from_file(config.MINIO_ACCESS_KEY_PATH),
                   secret_key=config.get_from_file(config.MINIO_SECRET_KEY_PATH), secure=False)
        if not mc.bucket_exists(name):
            try:
                mc.make_bucket(name)
                return True
            except InvalidBucketError as err:
                return False
            except BucketAlreadyOwnedByYou as err:
                return False
            except BucketAlreadyExists as err:
                return False
            except ResponseError as err:
                return False

    def remove_bucket_in_minio(self, name):
        mc = Minio(config.MINIO, access_key=config.get_from_file(config.MINIO_ACCESS_KEY_PATH),
                   secret_key=config.get_from_file(config.MINIO_SECRET_KEY_PATH), secure=False)
        if mc.bucket_exists(name):
            try:
                mc.remove_bucket(name)
                return True
            except NoSuchBucket as err:
                return False
            except ResponseError as err:
                return False

    def update_bucket_in_minio(self, new_name):
        success1 = self.create_bucket_in_minio(new_name)
        success2 = self.remove_bucket_in_minio(self.name)
        self.name = new_name
        return success1 and success2

    def _get_triggers_as_list(self):
        out = [t.as_json() for t in self.triggers]
        return out

    def as_json(self):
        out = {
                "id": self.id,
                "name": self.name,
               "description": self.description,
               "triggers": self._get_triggers_as_list()
               }
        return out


class BucketTrigger(db.Model):
    __tablename__ = 'bucket_triggers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bucket_id = db.Column(db.Integer, db.ForeignKey('bucket.id'))
    workflow = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.Enum('s3:ObjectCreated:*',
                                   's3:ObjectRemoved:*',
                                   's3:ObjectAccessed:*',
                                   'unspecified', name='event_types'))
    prefix = db.Column(db.String(255), nullable=False)
    suffix = db.Column(db.String(255), nullable=False)


    def __init__(self, workflow='', event_type='unspecified', prefix='', suffix=''):
        self.workflow = workflow
        self.event_type = event_type
        self.prefix = prefix
        self.suffix = suffix

    def as_json(self):
        out = {
                "id": self.id,
                "parent": self.bucket_id,
                "workflow": self.workflow,
                "event_type": self.event_type,
                "prefix": self.prefix,
                "suffix": self.suffix
              }
        return out
