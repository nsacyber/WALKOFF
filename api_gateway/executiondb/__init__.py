import enum
# from alembic import command
# from alembic.config import Config
from sqlalchemy import create_engine, event, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database

import api_gateway.config
from api_gateway.helpers import format_db_path

Execution_Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Execution_Base.metadata = MetaData(naming_convention=naming_convention)


class ExecutionDatabase(object):
    """Wrapper for the SQLAlchemy database connection object"""
    instance = None
    db_type = ""

    def __init__(self, execution_db_type, execution_db_path, execution_db_host="localhost"):
        # All of these imports are necessary
        from api_gateway.executiondb.parameter import Parameter
        from api_gateway.executiondb.action import Action
        from api_gateway.executiondb.branch import Branch
        from api_gateway.executiondb.condition import Condition
        from api_gateway.executiondb.position import Position
        from api_gateway.executiondb.transform import Transform
        from api_gateway.executiondb.trigger import Trigger
        from api_gateway.executiondb.global_variable import GlobalVariable
        from api_gateway.executiondb.workflow_variable import WorkflowVariable
        from api_gateway.executiondb.workflow import Workflow
        from api_gateway.executiondb.workflowresults import WorkflowStatus, ActionStatus

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

        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = scoped_session(Session)

        Execution_Base.metadata.bind = self.engine
        Execution_Base.metadata.create_all(self.engine)

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
def set_sqlite_pragma(dbapi_connection, connection_type):
    """Necessary for enforcing foreign key constraints in sqlite database
    """
    if 'sqlite' in ExecutionDatabase.db_type:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# TODO: Use common.message_types.StatusEnum for these
# class StatusEnum(enum.Enum):
#     running = "running"
#     paused = "paused"  # not currently implemented but may be if we see a use case
#     awaiting_data = "awaiting_data"  # possibly for triggers?
#     pending = "pending"
#     completed = "completed"
#     aborted = "aborted"
#
#
# class StatusEnum(enum.Enum):
#     executing = "executing"
#     awaiting_data = "awaiting_data"  # possibly for triggers?
#     success = "success"
#     failure = "failure"
#     aborted = "aborted"
