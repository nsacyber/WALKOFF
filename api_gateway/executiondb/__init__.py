# from alembic import command
# from alembic.config import Config

from datetime import datetime

from uuid import uuid4
from sqlalchemy import Column, String, Boolean, Enum, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from marshmallow_sqlalchemy import ModelSchema

from sqlalchemy import create_engine, event, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database

import api_gateway.config
from api_gateway.helpers import format_db_path
from common.message_types import StatusEnum

Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)


class ExecutionDatabase(object):
    """Wrapper for the SQLAlchemy database connection object"""
    instance = None
    db_type = ""

    def __init__(self, execution_db_type, execution_db_path, execution_db_host="localhost"):
        print(execution_db_type, execution_db_path, execution_db_host)
        # All of these imports are necessary
        from api_gateway.executiondb.returns import ReturnApi
        from api_gateway.executiondb.parameter import Parameter, ParameterApi
        from api_gateway.executiondb.action import Action, ActionApi
        from api_gateway.executiondb.appapi import AppApi
        from api_gateway.executiondb.branch import Branch
        from api_gateway.executiondb.condition import Condition
        from api_gateway.executiondb.transform import Transform
        # from api_gateway.executiondb.trigger import Trigger
        from api_gateway.executiondb.global_variable import GlobalVariable
        from api_gateway.executiondb.workflow_variable import WorkflowVariable
        from api_gateway.executiondb.workflow import Workflow
        from api_gateway.executiondb.workflowresults import WorkflowStatus, NodeStatus

        ExecutionDatabase.db_type = execution_db_type

        if 'sqlite' in execution_db_type:
            self.engine = create_engine(format_db_path(execution_db_type, execution_db_path),
                                        connect_args={'check_same_thread': False}, poolclass=NullPool)
        else:
            self.engine = create_engine(
                format_db_path(execution_db_type, execution_db_path, 'EXECUTION_DB_USERNAME', 'EXECUTION_DB_PASSWORD',
                               execution_db_host),
                poolclass=NullPool)
            if not database_exists(self.engine.url):
                try:
                    create_database(self.engine.url)
                except IntegrityError as e:
                    pass

        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

        session = sessionmaker()
        session.configure(bind=self.engine)
        self.session = scoped_session(session)

        Base.metadata.bind = self.engine
        Base.metadata.create_all(self.engine)

        # alembic_cfg = Config(api_gateway.config.Config.ALEMBIC_CONFIG, ini_section="execution",
        #                      attributes={'configure_logger': False})
        # command.stamp(alembic_cfg, "head")

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(ExecutionDatabase, cls).__new__(cls)
        return cls.instance

    def tear_down(self):
        """Clean up the database
        """
        self.session.rollback()
        self.connection.close()
        self.engine.dispose()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_type):  # noqa
    """Necessary for enforcing foreign key constraints in sqlite database
    """
    if 'sqlite' in ExecutionDatabase.db_type:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class BaseSchema(ModelSchema):
    """
    Base schema, attaches ExecutionDatabase session to model on load.
    """
    def load(self, data, session=None, instance=None, *args, **kwargs):
        session = ExecutionDatabase.instance.session
        # ToDo: Automatically find and use instance if 'id' (or key) is passed
        return super(BaseSchema, self).load(data, session=session, instance=instance, *args, **kwargs)


class IDMixin(object):
    """
    Base model that provides for a uuid primary key
    """
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # def __init__(self, id_=None):
    #     # ToDo: do better validation
    #     if id_:
    #         self.id_ = id_

    # def __repr__(self):
    #     from .model_schema_map import dump_element
    #
    #     representation = dump_element(self)
    #     out = '<{0} at {1} : '.format(self.__class__.__name__, hex(id(self)))
    #     first = True
    #     for key, value in representation.items():
    #         if self.__is_list_of_dicts_with_uids(value):
    #             out += ', {0}={1}'.format(key, [list_value['id_'] for list_value in value])
    #         else:
    #             out += ', {0}={1}'.format(key, value)
    #
    #         if first:
    #             out = out.replace(" ,", "")
    #             first = False
    #
    #     out += '>'
    #     return out

    # @staticmethod
    # def __is_list_of_dicts_with_uids(value):
    #     return (isinstance(value, list)
    #             and all(isinstance(list_value, dict) and 'id_' in list_value for list_value in value))


class VariableMixin(IDMixin):
    """
    Base model for variables (Parameters, Workflow Variables, Global Variables)
    """
    name = Column(String(80), nullable=False)
    value = Column(JSON)

    def __init__(self, name, value=None, **kwargs):
        super(IDMixin, self).__init__(**kwargs)
        self.name = name
        self.value = value


class ValidatableMixin(IDMixin):
    """
    Base model for validatables (elements that can contain errors)
    """
    errors = Column(ARRAY(String))
    is_valid = Column(Boolean, default=True)
    children = []

    def __init__(self, errors=None, **kwargs):
        super(IDMixin, self).__init__(**kwargs)
        self.errors = errors if errors else []
        self.is_valid = self._is_valid()

    def validate(self):
        raise NotImplementedError("Validatable must implement self.validate().")

    def _is_valid(self):
        if self.errors:
            return False
        for child in self.children:
            child = getattr(self, child, None)
            if isinstance(child, list):
                for actual_child in child:
                    if not actual_child._is_valid():
                        return False
            elif child is not None:
                if not child._is_valid():
                    return False
        return True


class StatusMixin(object):
    name = Column(String(80), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False)
    started_at = Column(String, default="")
    completed_at = Column(String, default="")
