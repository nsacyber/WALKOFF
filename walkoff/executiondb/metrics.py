from sqlalchemy_utils import UUIDType

from sqlalchemy import Column, Integer, ForeignKey, String, Float
from sqlalchemy.orm import relationship
from walkoff.executiondb import Execution_Base


class AppMetric(Execution_Base):
    __tablename__ = 'app_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    app = Column(String, nullable=False)
    count = Column(Integer)
    actions = relationship('ActionMetric', cascade='all, delete, delete-orphan')

    def __init__(self, app, actions=None):
        self.app = app
        self.actions = actions if actions else []
        self.count = 0

    def get_action_by_id(self, action_id):
        for action in self.actions:
            if action.action_id == action_id:
                return action
        return None

    def as_json(self):
        ret = {"name": self.app,
               "count": self.count}
        actions_list = []
        for action in self.actions:
            actions_list.append(action.as_json())
        ret["actions"] = actions_list


class ActionMetric(Execution_Base):
    __tablename__ = 'action_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(UUIDType, nullable=False)
    action_name = Column(String(255), nullable=False)
    app_metric_id = Column(Integer, ForeignKey('app_metric.id'))
    action_statuses = relationship('ActionStatusMetric', cascade='all, delete, delete-orphan')

    def __init__(self, action_id, name, action_statuses=None):
        self.action_id = action_id
        self.action_name = name
        self.action_statuses = action_statuses if action_statuses else []

    def get_action_status(self, status):
        for action_status in self.action_statuses:
            if action_status.status == status:
                return action_status
        return None

    def as_json(self):
        ret = {"name": self.action_name}
        for action_status in self.action_statuses:
            if action_status.status == "success":
                ret["success_metrics"] = action_status.as_json()
            else:
                ret["error_metrics"] = action_status.as_json()
        return ret


class ActionStatusMetric(Execution_Base):
    __tablename__ = 'action_status_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(10))
    count = Column(Integer)
    avg_time = Column(Float)
    action_metric_id = Column(Integer, ForeignKey('action_metric.id'))

    def __init__(self, status, avg_time):
        self.status = status
        self.avg_time = avg_time
        self.count = 1

    def update(self, execution_time):
        self.count += 1
        self.avg_time = (self.avg_time + execution_time) / 2

    def as_json(self):
        ret = {"count": self.count,
               "avg_time": str(self.avg_time)}
        return ret


class WorkflowMetric(Execution_Base):
    __tablename__ = 'workflow_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(UUIDType, nullable=False)
    workflow_name = Column(String(255), nullable=False)
    count = Column(Integer)
    avg_time = Column(Float)

    def __init__(self, workflow_id, workflow_name, avg_time):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.avg_time = avg_time
        self.count = 1

    def update(self, execution_time):
        self.count += 1
        self.avg_time = (self.avg_time + execution_time) / 2

    def as_json(self):
        ret = {"name": self.workflow_name,
               "count": self.count,
               "avg_time": str(self.avg_time)}
        return ret
