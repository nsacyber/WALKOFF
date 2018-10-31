import json
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import UUIDType

from walkoff.executiondb import Execution_Base, WorkflowStatusEnum, ActionStatusEnum
from walkoff.helpers import utc_as_rfc_datetime


class WorkflowStatus(Execution_Base):
    """ORM for a Status of a Workflow in the database

    Attributes:
        execution_id (UUID): Execution ID of the Workflow
        workflow_id (UUID): ID of the Workflow
        name (str): Name of the Workflow
        status (str): Status of the Workflow
        started_at (datetime): Time the Workflow started
        completed_at (datetime): Time the Workflow ended
        user (str): The user who initially executed this workflow
        _action_statuses (list[ActionStatus]): A list of ActionStatus objects for this WorkflowStatus
    """
    __tablename__ = 'workflow_status'
    execution_id = Column(UUIDType(binary=False), primary_key=True)
    workflow_id = Column(UUIDType(binary=False), nullable=False)
    name = Column(String, nullable=False)
    status = Column(Enum(WorkflowStatusEnum, name='WorkflowStatusEnum'), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    user = Column(String)
    _action_statuses = relationship('ActionStatus', backref=backref('_workflow_status'), cascade='all, delete-orphan')

    def __init__(self, execution_id, workflow_id, name, user=None):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.name = name
        self.status = WorkflowStatusEnum.pending
        self.user = user

    def running(self):
        """Sets the status to running"""
        self.started_at = datetime.utcnow()
        self.status = WorkflowStatusEnum.running

    def paused(self):
        """Sets the status to paused"""
        self.status = WorkflowStatusEnum.paused

    def awaiting_data(self):
        """Sets the status to awaiting data"""
        self.status = WorkflowStatusEnum.awaiting_data
        if self._action_statuses:
            self._action_statuses[-1].awaiting_data()

    def completed(self):
        """Sets the status to completed"""
        self.completed_at = datetime.utcnow()
        self.status = WorkflowStatusEnum.completed

    def aborted(self):
        """Sets the status to aborted"""
        self.completed_at = datetime.utcnow()
        self.status = WorkflowStatusEnum.aborted
        if self._action_statuses:
            self._action_statuses[-1].aborted()

    def add_action_status(self, action_status):
        """Adds an ActionStatus

        Args:
            action_status (ActionStatus): The ActionStatus to add
        """
        self._action_statuses.append(action_status)

    def as_json(self, full_actions=False):
        """Gets the JSON representation of the WorkflowStatus

        Args:
            full_actions (bool, optional): Get the full Action objects as well? Defaults to False

        Returns:
            The JSON representation of the object
        """
        ret = {"execution_id": str(self.execution_id),
               "workflow_id": str(self.workflow_id),
               "name": self.name,
               "status": self.status.name}
        if self.user:
            ret["user"] = self.user
        if self.started_at:
            ret["started_at"] = utc_as_rfc_datetime(self.started_at)
        if self.status in [WorkflowStatusEnum.completed, WorkflowStatusEnum.aborted]:
            ret["completed_at"] = utc_as_rfc_datetime(self.completed_at)
        if full_actions:
            ret["action_statuses"] = [action_status.as_json() for action_status in self._action_statuses]
        elif self._action_statuses and self.status != WorkflowStatusEnum.completed:
            current_action = self._action_statuses[-1]
            ret['current_action'] = current_action.as_json(summary=True)

        return ret


class ActionStatus(Execution_Base):
    """ORM for an Action event in the database

    Attributes:
        execution_id (UUID): The execution ID of the Action
        action_id (UUID): The ID of the Action
        name (str): The name of the Action
        app_name (str): The App name for the Action
        action_name (str): The Action name for the Action
        result (str): The result of the Action
        arguments (str): The Arguments for the Action, in string representation
        status (ActionStatusEnum): The status of the Action
        started_at (datetime): The time the Action started
        completed_at (datetime): The time the Action completed
        _workflow_status_id (UUID): The FK ID of the WorkflowStatus
    """
    __tablename__ = 'action_status'
    execution_id = Column(UUIDType(binary=False), primary_key=True)
    action_id = Column(UUIDType(binary=False), nullable=False)
    name = Column(String, nullable=False)
    app_name = Column(String, nullable=False)
    action_name = Column(String, nullable=False)
    result = Column(String)
    arguments = Column(String)
    status = Column(Enum(ActionStatusEnum, name='ActionStatusEnum'), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    _workflow_status_id = Column(UUIDType(binary=False), ForeignKey('workflow_status.execution_id'))

    def __init__(self, execution_id, action_id, name, app_name, action_name, arguments=None):
        self.execution_id = execution_id
        self.action_id = action_id
        self.name = name
        self.app_name = app_name
        self.action_name = action_name
        self.arguments = arguments
        self.status = ActionStatusEnum.executing

    def aborted(self):
        """Sets status to aborted"""
        if self.status == ActionStatusEnum.awaiting_data:
            self.status = ActionStatusEnum.aborted

    def running(self):
        """Sets status to running"""
        self.status = ActionStatusEnum.executing

    def awaiting_data(self):
        """Sets status to awaiting data"""
        self.status = ActionStatusEnum.awaiting_data

    def completed_success(self, data):
        """Sets status to completed successfully"""
        self.status = ActionStatusEnum.success
        self.result = json.dumps(data['result'])
        self.completed_at = datetime.utcnow()

    def completed_failure(self, data):
        """Sets status to completed unsuccessfully"""
        self.status = ActionStatusEnum.failure
        self.result = json.dumps(data['result'])
        self.completed_at = datetime.utcnow()

    def as_json(self, summary=False):
        """Gets the JSON representation of the object

        Args:
            summary (bool, optional): Only get a limited JSON? Defaults to False

        Returns:
            (dict): The JSON representation of the object
        """
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
             "started_at": utc_as_rfc_datetime(self.started_at)})
        if self.status in [ActionStatusEnum.success, ActionStatusEnum.failure]:
            ret["result"] = json.loads(self.result)
            ret["completed_at"] = utc_as_rfc_datetime(self.completed_at)
        return ret
