import json
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship, backref

from walkoff.coredb import Device_Base, WorkflowStatusEnum, ActionStatusEnum
from sqlalchemy_utils import UUIDType


class WorkflowStatus(Device_Base):
    """Case ORM for a Workflow event in the database
    """
    __tablename__ = 'workflow_status'
    execution_id = Column(UUIDType(), primary_key=True)
    workflow_id = Column(UUIDType(), nullable=False)
    name = Column(String, nullable=False)
    status = Column(Enum(WorkflowStatusEnum), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    _action_statuses = relationship('ActionStatus', backref=backref('_workflow_status'), cascade='all, delete-orphan')

    def __init__(self, execution_id, workflow_id, name):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.name = name
        self.status = WorkflowStatusEnum.pending

    def running(self):
        self.started_at = datetime.utcnow()
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

    def as_json(self, full_actions=False):
        ret = {"execution_id": str(self.execution_id),
               "workflow_id": str(self.workflow_id),
               "name": self.name,
               "status": self.status.name}
        if self.started_at:
            ret["started_at"] = self.started_at.isoformat()
        if self.status in [WorkflowStatusEnum.completed, WorkflowStatusEnum.aborted]:
            ret["completed_at"] = self.completed_at.isoformat()
        if full_actions:
            ret["action_statuses"] = [action_status.as_json() for action_status in self._action_statuses]
        elif self._action_statuses:
            current_action = self._action_statuses[-1]
            ret['current_action'] = current_action.as_json(summary=True)

        return ret



class ActionStatus(Device_Base):
    """ORM for an Action event in the database
    """
    __tablename__ = 'action_status'
    execution_id = Column(UUIDType(), primary_key=True)
    action_id = Column(UUIDType(), nullable=False)
    name = Column(String, nullable=False)
    app_name = Column(String, nullable=False)
    action_name = Column(String, nullable=False)
    result = Column(String)
    arguments = Column(String)
    status = Column(Enum(ActionStatusEnum), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    _workflow_status_id = Column(UUIDType(), ForeignKey('workflow_status.execution_id'))

    def __init__(self, execution_id, action_id, name, app_name, action_name, arguments=None):
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

    def as_json(self, summary=False):
        ret = {"execution_id": str(self.execution_id),
               "action_id": str(self.action_id),
               "name": self.name,
               "app_name": self.app_name,
               "action_name": self.action_name}
        if summary:
            return ret
        ret.update(
            {"arguments": json.loads(self.arguments) if self.arguments else [],
             "status": self.status.name,
             "started_at": self.started_at.isoformat()})
        if self.status in [ActionStatusEnum.success, ActionStatusEnum.failure]:
            ret["result"] = json.loads(self.result)
            ret["completed_at"] = self.completed_at.isoformat()
        return ret
