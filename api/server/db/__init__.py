# from alembic import command
# from alembic.config import Config
import asyncio
import datetime

from starlette.requests import Request
from sqlalchemy import create_engine, event, MetaData, Column, DateTime
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database

import motor.motor_asyncio
import pymongo

from common.config import config, static
from api.server.utils.helpers import format_db_path


Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)


class DBEngine(object):
    """Wrapper for the SQLAlchemy database connection object"""

    def __init__(self):
        # Import all modules here for SQLAlchemy to correctly initialize
        # from api.server.db.appapi import AppApi

        self.engine = create_engine(
            format_db_path(config.DB_TYPE, config.EXECUTION_DB_NAME,
                           config.DB_USERNAME, config.get_from_file(config.POSTGRES_KEY_PATH),
                           config.DB_HOST),
            poolclass=NullPool, isolation_level="AUTOCOMMIT")

        if not database_exists(self.engine.url):
            try:
                create_database(self.engine.url)
            except IntegrityError as e:
                pass

        # self.connection = self.engine.connect()
        # self.transaction = self.connection.begin()

        self.session_maker = sessionmaker(bind=self.engine)
        # self.session = scoped_session(session)
        Base.metadata.bind = self.engine
        Base.metadata.create_all(self.engine)

    def current_timestamp(self):
        return datetime.datetime.now()
        # alembic_cfg = Config(api_gateway.config.Config.ALEMBIC_CONFIG, ini_section="execution",
        #                      attributes={'configure_logger': False})
        # command.stamp(alembic_cfg, "head")


def get_db(request: Request):
    return request.state.db


db = DBEngine()

#
# class TrackModificationsMixIn(Base):
#     __tablename__ = 'mixin'
#     created_at = Column(DateTime, default=db.current_timestamp())
#     modified_at = Column(DateTime, default=db.current_timestamp(), onupdate=db.current_timestamp())


# class BaseSchema(ModelSchema):
#     """
#     Base schema, attaches ExecutionDatabase session to model on load.
#     """
#
#     @pre_load
#     def set_nested_session(self, data):
#         """Allow nested schemas to use the parent schema's session. This is a
#         longstanding bug with marshmallow-sqlalchemy.
#
#         https://github.com/marshmallow-code/marshmallow-sqlalchemy/issues/67
#         https://github.com/marshmallow-code/marshmallow/issues/658#issuecomment-328369199
#         """
#         nested_fields = {k: v for k, v in self.fields.items() if type(v) == fields.Nested}
#         for field in nested_fields.values():
#             field.schema.session = self.session
#
#     def load(self, data, session=None, instance=None, *args, **kwargs):
#         session = db.session_maker
#         # ToDo: Automatically find and use instance if 'id' (or key) is passed
#         return super(BaseSchema, self).load(data, session=session, instance=instance, *args, **kwargs)
#

class MongoEngine(object):
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(username=config.DB_USERNAME,
                                                             password=config.get_from_file(config.MONGO_KEY_PATH),
                                                             host=config.MONGO_HOST)

    async def init_db(self):
        await self.client.walkoff_db.apps.create_index([("id_", pymongo.ASCENDING),
                                                        ("name", pymongo.ASCENDING)],
                                                       unique=True)

        await self.client.walkoff_db.workflows.create_index([("id_", pymongo.ASCENDING),
                                                             ("name", pymongo.ASCENDING)],
                                                            unique=True)

    def collection_from_url(self, path: str):
        parts = path.split("/")
        if len(parts) >= 4:
            resource = parts[3]
            return self.client.walkoff_db[resource]
        else:
            return None


def get_mongo_c(request: Request):
    return request.state.mongo_c


mongo = MongoEngine()
