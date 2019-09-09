# from alembic import command
# from alembic.config import Config


from starlette.requests import Request
from marshmallow_sqlalchemy import ModelSchema

from sqlalchemy import create_engine, event, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database

from common.config import config
from api_gateway.helpers import format_db_path

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
    instance = None

    def __init__(self):
        # Import all modules here for SQLAlchemy to correctly initialize
        from api.server.db.appapi import AppApi

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
        #
        self.session_maker = sessionmaker(bind=self.engine)
        # self.session = scoped_session(session)

        Base.metadata.bind = self.engine
        Base.metadata.create_all(self.engine)

        # alembic_cfg = Config(api_gateway.config.Config.ALEMBIC_CONFIG, ini_section="execution",
        #                      attributes={'configure_logger': False})
        # command.stamp(alembic_cfg, "head")


def get_db(request: Request):
    return request.state.db

db = DBEngine()

# class BaseSchema(ModelSchema):
#     """
#     Base schema, attaches ExecutionDatabase session to model on load.
#     """
#
#     def load(self, data, session=None, instance=None, *args, **kwargs):
#         session = db.session_maker
#         # ToDo: Automatically find and use instance if 'id' (or key) is passed
#         return super(BaseSchema, self).load(data, session=session, instance=instance, *args, **kwargs)
