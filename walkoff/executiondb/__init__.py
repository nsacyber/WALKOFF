import os

import enum
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database

from walkoff.helpers import format_db_path

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
        from walkoff.executiondb.device import App, Device, DeviceField, EncryptedDeviceField
        from walkoff.executiondb.argument import Argument
        from walkoff.executiondb.conditionalexpression import ConditionalExpression
        from walkoff.executiondb.action import Action
        from walkoff.executiondb.branch import Branch
        from walkoff.executiondb.condition import Condition
        from walkoff.executiondb.playbook import Playbook
        from walkoff.executiondb.position import Position
        from walkoff.executiondb.transform import Transform
        from walkoff.executiondb.environment_variable import EnvironmentVariable
        from walkoff.executiondb.workflow import Workflow
        from walkoff.executiondb.saved_workflow import SavedWorkflow
        from walkoff.executiondb.workflowresults import WorkflowStatus, ActionStatus
        from walkoff.executiondb.metrics import AppMetric, WorkflowMetric, ActionMetric, ActionStatusMetric

        ExecutionDatabase.db_type = execution_db_type

        if 'sqlite' in execution_db_type:
            self.engine = create_engine(format_db_path(execution_db_type, execution_db_path),
                                        connect_args={'check_same_thread': False}, poolclass=NullPool)
        else:
            self.engine = create_engine(
                format_db_path(execution_db_type, execution_db_path, 'WALKOFF_DB_USERNAME', 'WALKOFF_DB_PASSWORD',
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

        alembic_cfg = Config(os.path.abspath("alembic.ini"), ini_section="execution", attributes={'configure_logger': False})
        command.stamp(alembic_cfg, "head")

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
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Necessary for enforcing foreign key constraints in sqlite database
    """
    if 'sqlite' in ExecutionDatabase.db_type:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class WorkflowStatusEnum(enum.Enum):
    running = 1
    paused = 2
    awaiting_data = 3
    pending = 4
    completed = 5
    aborted = 6


class ActionStatusEnum(enum.Enum):
    executing = 1
    awaiting_data = 2
    success = 3
    failure = 4
    aborted = 5
