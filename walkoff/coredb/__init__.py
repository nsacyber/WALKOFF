from sqlalchemy.ext.declarative import declarative_base
import enum

Device_Base = declarative_base()


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
