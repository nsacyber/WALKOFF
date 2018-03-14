import enum
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

import walkoff.config.config
import walkoff.config.paths
from walkoff.helpers import format_db_path

Execution_Base = declarative_base()


class ExecutionDatabase(object):
    """Wrapper for the SQLAlchemy database connection object
    """

    __instance = None

    def __init__(self):
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
        from walkoff.executiondb.workflow import Workflow
        from walkoff.executiondb.saved_workflow import SavedWorkflow
        from walkoff.executiondb.workflowresults import WorkflowStatus, ActionStatus

        self.engine = create_engine(format_db_path(
            walkoff.config.config.device_db_type, walkoff.config.paths.execution_db_path), poolclass=NullPool)
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = scoped_session(Session)

        Execution_Base.metadata.bind = self.engine
        Execution_Base.metadata.create_all(self.engine)

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(ExecutionDatabase, cls).__new__(cls)
        return cls.__instance

    def tear_down(self):
        self.session.rollback()
        self.connection.close()
        self.engine.dispose()


execution_db = None
"""The SQLAlchemy engine/connection object for the execution database
"""


class WorkflowStatusEnum(enum.Enum):
    pending = 1
    running = 2
    paused = 3
    awaiting_data = 4
    completed = 5
    aborted = 6


class ActionStatusEnum(enum.Enum):
    executing = 1
    awaiting_data = 2
    success = 3
    failure = 4
    aborted = 5
