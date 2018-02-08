import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship, backref

from walkoff.coredb import Device_Base, WorkflowStatusEnum, ActionStatusEnum
from walkoff.dbtypes import Guid


class WorkflowStatus(Device_Base):
    """Case ORM for a Workflow event in the database
    """
    __tablename__ = 'workflow_status'
    execution_id = Column(Guid(), primary_key=True)
    workflow_id = Column(Guid(), nullable=False)
    name = Column(String, nullable=False)
    status = Column(Enum(WorkflowStatusEnum), nullable=False)
    started_at = Column(DateTime, default=func.current_timestamp())
    completed_at = Column(DateTime)
    _action_statuses = relationship('ActionStatus', backref=backref('_workflow_status'), cascade='all, delete-orphan')

    def __init__(self, execution_id, workflow_id, name):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.name = name
        self.status = WorkflowStatusEnum.pending

    def running(self):
        self.status = WorkflowStatusEnum.running

    def paused(self):
        self.status = WorkflowStatusEnum.paused

    def awaiting_data(self):
        self.status = WorkflowStatusEnum.awaiting_data

    def completed(self):
        self.completed_at = datetime.utcnow()
        self.status = WorkflowStatusEnum.completed

    def aborted(self):
        self.completed_at = datetime.utcnow()
        self.status = WorkflowStatusEnum.aborted

    def as_json(self):
        ret = {"execution_id": self.execution_id,
               "workflow_id": self.workflow_id,
               "name": self.name,
               "status": self.status,
               "started_at": str(self.started_at),
               "action_statuses": [action_status.as_json() for action_status in self._action_statuses]}
        if self.status in [WorkflowStatusEnum.completed, WorkflowStatusEnum.aborted]:
            ret["completed_at"] = str(self.completed_at)
        return ret


class ActionStatus(Device_Base):
    """ORM for an Action event in the database
    """
    __tablename__ = 'action_status'
    execution_id = Column(Guid(), primary_key=True)
    action_id = Column(Guid(), nullable=False)
    name = Column(String, nullable=False)
    app_name = Column(String, nullable=False)
    action_name = Column(String, nullable=False)
    result = Column(String)
    arguments = Column(String)
    status = Column(Enum(ActionStatusEnum), nullable=False)
    started_at = Column(DateTime, default=func.current_timestamp())
    completed_at = Column(DateTime)
    _workflow_status_id = Column(Integer, ForeignKey('workflow_status.execution_id'))

    def __init__(self, execution_id, action_id, name, app_name, action_name, arguments):
        self.execution_id = execution_id
        self.action_id = action_id
        self.name = name
        self.app_name = app_name
        self.action_name = action_name
        self.arguments = arguments
        self.status = ActionStatusEnum.executing

    def running(self):
        self.status = ActionStatusEnum.executing

    def paused(self):
        self.status = ActionStatusEnum.paused

    def awaiting_data(self):
        self.status = ActionStatusEnum.awaiting_data

    def completed_success(self, data):
        self.status = ActionStatusEnum.success
        self.result = json.dumps(data['result'])
        self.completed_at = datetime.utcnow()

    def completed_failure(self, data):
        self.status = ActionStatusEnum.failure
        self.result = json.dumps(data['result'])
        self.completed_at = datetime.utcnow()

    def as_json(self):
        ret = {"execution_id": self.execution_id,
               "action_id": self.action_id,
               "name": self.name,
               "app_name": self.app_name,
               "action_name": self.action_name,
               "arguments": json.loads(self.arguments),
               "status": self.status,
               "started_at": str(self.started_at)
               }
        if self.status in [ActionStatusEnum.success, ActionStatusEnum.failure]:
            ret["result"] = json.loads(self.result)
            ret["completed_at"] = str(self.completed_at)
        return ret
