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
    paused = 2
    awaiting_data = 3
    success = 4
    failure = 5
