import os
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

        #MINIO CONFIG
        # self.minio_address = os.getenv("MINIO_ADDRESS")
        self.minio_address = "minio:9000"
        self.minio_access_key = "test"
        self.minio_secret_key = "secretkey"
        self.minio_secure = False
        self.minio_region = None

        if triggers is not None:
            for t in set(triggers):
                self.triggers.append(BucketTrigger(**t))

    @orm.reconstructor
    def init_on_load(self):
        self.minio_address = "minio:9000"
        self.minio_access_key = "test"
        self.minio_secret_key = "secretkey"
        self.minio_secure = False
        self.minio_region = None

    def create_bucket_in_minio(self, name):
        mc = Minio(self.minio_address, access_key=self.minio_access_key, secret_key=self.minio_secret_key,
                   secure=self.minio_secure, region=self.minio_region)
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
        mc = Minio(self.minio_address, access_key=self.minio_access_key, secret_key=self.minio_secret_key,
                   secure=self.minio_secure, region=self.minio_region)
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
