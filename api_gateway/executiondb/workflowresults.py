import json
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb.schemas import ExecutionBaseSchema

from common.message_types import StatusEnum
from api_gateway.executiondb import Execution_Base
from api_gateway.helpers import utc_as_rfc_datetime


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
        action_statuses (list[ActionStatus]): A list of ActionStatusMessage objects for this WorkflowStatusMessage
    """
    __tablename__ = 'workflow_status'
    execution_id = Column(UUIDType(binary=False), primary_key=True)
    workflow_id = Column(UUIDType(binary=False), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # ToDo: revisit this and make this a real enum
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    user = Column(String)
    # TODO: change these on the db model to be keyed by ID (use an association proxy)
    action_statuses = relationship('ActionStatus', backref=backref("execution_id"), passive_deletes=True,
                                   cascade='all, delete-orphan')

    def __init__(self, execution_id, workflow_id, name, status=StatusEnum.PENDING, started_at=None, completed_at=None,
                 user=None, action_statuses=None):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.name = name
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.user = user
        self.action_statuses = action_statuses if action_statuses else []

    def running(self):
        """Sets the status to running"""
        self.started_at = datetime.utcnow()
        self.status = StatusEnum.EXECUTING

    def paused(self):
        """Sets the status to paused"""
        self.status = StatusEnum.PAUSED

    def awaiting_data(self):
        """Sets the status to awaiting data"""
        self.status = StatusEnum.AWAITING_DATA
        if self.action_statuses:
            self.action_statuses[-1].awaiting_data()

    def completed(self):
        """Sets the status to completed"""
        self.completed_at = datetime.utcnow()
        self.status = StatusEnum.COMPLETED

    def aborted(self):
        """Sets the status to aborted"""
        self.completed_at = datetime.utcnow()
        self.status = StatusEnum.ABORTED
        if self.action_statuses:
            self.action_statuses[-1].aborted()

    def add_action_status(self, action_status):
        """Adds an ActionStatusMessage

        Args:
            action_status (ActionStatus): The ActionStatusMessage to add
        """
        self.action_statuses.append(action_status)

    def as_json(self, full_actions=False):
        """Gets the JSON representation of the WorkflowStatusMessage

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
        if self.status in [StatusEnum.COMPLETED, StatusEnum.ABORTED]:
            ret["completed_at"] = utc_as_rfc_datetime(self.completed_at)
        if full_actions:
            ret["action_statuses"] = [action_status.as_json() for action_status in self.action_statuses]
        elif self.action_statuses and self.status != StatusEnum.COMPLETED:
            current_action = self.action_statuses[-1]
            ret['current_action'] = current_action.as_json(summary=True)

        return ret


class ActionStatus(Execution_Base):
    """ORM for an Action event in the database

    Attributes:
        action_id (UUID): The ID of the Action
        label (str): The label of the Action
        app_name (str): The App name for the Action
        name (str): The Action name for the Action
        result (str): The result of the Action
        status (StatusEnum): The status of the Action
        started_at (datetime): The time the Action started
        completed_at (datetime): The time the Action completed
        _workflow_status_id (UUID): The FK ID of the WorkflowStatusMessage
    """
    __tablename__ = 'action_status'
    combined_id = Column(String, primary_key=True)
    action_id = Column(UUIDType(binary=False), nullable=False)
    name = Column(String, nullable=False)
    app_name = Column(String, nullable=False)
    label = Column(String, nullable=False)
    result = Column(String)
    arguments = Column(String)
    status = Column(String, nullable=False)  # ToDo: revisit this and make this a real enum
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    workflow_execution_id = Column(UUIDType(binary=False),
                                   ForeignKey('workflow_status.execution_id', ondelete='CASCADE'))

    def __init__(self, combined_id, action_id, name, app_name, label, result=None, arguments=None,
                 status=StatusEnum.EXECUTING, started_at=None, completed_at=None):
        self.combined_id = combined_id
        self.action_id = action_id
        self.name = name
        self.app_name = app_name
        self.label = label
        self.result = result
        self.arguments = arguments
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at

    def aborted(self):
        """Sets status to aborted"""
        if self.status == StatusEnum.AWAITING_DATA:
            self.status = StatusEnum.ABORTED

    def running(self):
        """Sets status to running"""
        self.status = StatusEnum.EXECUTING

    def awaiting_data(self):
        """Sets status to awaiting data"""
        self.status = StatusEnum.AWAITING_DATA

    def completed_success(self, data):
        """Sets status to completed successfully"""
        self.status = StatusEnum.SUCCESS
        self.result = json.dumps(data['result'])
        self.completed_at = datetime.utcnow()

    def completed_failure(self, data):
        """Sets status to completed unsuccessfully"""
        self.status = StatusEnum.FAILURE
        self.result = json.dumps(data['result'])
        self.completed_at = datetime.utcnow()

    def as_json(self, summary=False):
        """Gets the JSON representation of the object

        Args:
            summary (bool, optional): Only get a limited JSON? Defaults to False

        Returns:
            (dict): The JSON representation of the object
        """
        ret = {"execution_id": str(self.combined_id),
               "action_id": str(self.action_id),
               "label": self.name,
               "app_name": self.app_name,
               "name": self.action_name}
        if summary:
            return ret
        ret.update(
            {"arguments": json.loads(self.arguments) if self.arguments else [],
             "status": self.status.name,
             "started_at": utc_as_rfc_datetime(self.started_at)})
        if self.status in [StatusEnum.SUCCESS, StatusEnum.FAILURE]:
            ret["result"] = json.loads(self.result)
            ret["completed_at"] = utc_as_rfc_datetime(self.completed_at)
        return ret


class ActionStatusSchema(ExecutionBaseSchema):
    """
    Schema for ActionStatusMessage
    """
    action_id = field_for(ActionStatus, 'action_id', required=True)
    name = field_for(ActionStatus, 'name', required=True)
    app_name = field_for(ActionStatus, 'app_name', required=True)
    label = field_for(ActionStatus, 'label', required=True)
    result = field_for(ActionStatus, 'result')
    status = field_for(ActionStatus, 'status', required=True)
    started_at = field_for(ActionStatus, 'started_at')
    completed_at = field_for(ActionStatus, 'completed_at')

    class Meta:
        model = ActionStatus
        unknown = EXCLUDE


class ActionStatusSummarySchema(ExecutionBaseSchema):
    """
    Summary Schema for ActionStatusMessage
    """
    action_id = field_for(ActionStatus, 'action_id', required=True)
    name = field_for(ActionStatus, 'name', required=True)
    app_name = field_for(ActionStatus, 'app_name', required=True)
    label = field_for(ActionStatus, 'label', required=True)

    class Meta:
        model = ActionStatus
        unknown = EXCLUDE


class WorkflowStatusSchema(ExecutionBaseSchema):
    """
    Schema for WorkflowStatusMessage
    """
    execution_id = field_for(WorkflowStatus, 'execution_id', required=True)
    workflow_id = field_for(WorkflowStatus, 'workflow_id', required=True)
    name = field_for(WorkflowStatus, 'name', required=True)
    status = field_for(WorkflowStatus, 'status', required=True)
    started_at = field_for(WorkflowStatus, 'started_at')
    completed_at = field_for(WorkflowStatus, 'completed_at')
    user = field_for(WorkflowStatus, 'user')
    action_statuses = fields.Nested(ActionStatusSchema, many=True)

    class Meta:
        model = WorkflowStatus
        unknown = EXCLUDE


class WorkflowStatusSummarySchema(ExecutionBaseSchema):
    """
    Summary Schema for WorkflowStatusMessage
    """
    execution_id = field_for(WorkflowStatus, 'execution_id', required=True)
    workflow_id = field_for(WorkflowStatus, 'workflow_id', required=True)
    name = field_for(WorkflowStatus, 'name', required=True)
    status = field_for(WorkflowStatus, 'status', required=True)
    started_at = field_for(WorkflowStatus, 'started_at')
    completed_at = field_for(WorkflowStatus, 'completed_at')
    user = field_for(WorkflowStatus, 'user')
    action_status = fields.Nested(ActionStatusSchema)

    class Meta:
        model = WorkflowStatus
        unknown = EXCLUDE
