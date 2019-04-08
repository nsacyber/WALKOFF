import json
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
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
        node_statuses (list[NodeStatus]): A list of NodeStatusMessage objects for this WorkflowStatusMessage
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
    node_statuses = relationship('NodeStatus', backref=backref("execution_id"), passive_deletes=True,
                                 cascade='all, delete-orphan')

    def __init__(self, execution_id, workflow_id, name, status=StatusEnum.PENDING, started_at=None, completed_at=None,
                 user=None, node_statuses=None):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.name = name
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.user = user
        self.node_statuses = node_statuses if node_statuses else []

    # def running(self):
    #     """Sets the status to running"""
    #     self.started_at = datetime.utcnow()
    #     self.status = StatusEnum.EXECUTING
    #
    # def paused(self):
    #     """Sets the status to paused"""
    #     self.status = StatusEnum.PAUSED
    #
    # def awaiting_data(self):
    #     """Sets the status to awaiting data"""
    #     self.status = StatusEnum.AWAITING_DATA
    #     if self.node_statuses:
    #         self.node_statuses[-1].awaiting_data()
    #
    # def completed(self):
    #     """Sets the status to completed"""
    #     self.completed_at = datetime.utcnow()
    #     self.status = StatusEnum.COMPLETED
    #
    # def aborted(self):
    #     """Sets the status to aborted"""
    #     self.completed_at = datetime.utcnow()
    #     self.status = StatusEnum.ABORTED
    #     if self.node_statuses:
    #         self.node_statuses[-1].aborted()
    #
    # def add_node_status(self, node_status):
    #     """Adds an NodeStatusMessage
    #
    #     Args:
    #         node_status (NodeStatus): The NodeStatusMessage to add
    #     """
    #     self.node_statuses.append(node_status)
    #
    # def as_json(self, full_nodes=False):
    #     """Gets the JSON representation of the WorkflowStatusMessage
    #
    #     Args:
    #         full_nodes (bool, optional): Get the full node objects as well? Defaults to False
    #
    #     Returns:
    #         The JSON representation of the object
    #     """
    #     ret = {"execution_id": str(self.execution_id),
    #            "workflow_id": str(self.workflow_id),
    #            "name": self.name,
    #            "status": self.status.name}
    #
    #     if self.user:
    #         ret["user"] = self.user
    #     if self.started_at:
    #         ret["started_at"] = utc_as_rfc_datetime(self.started_at)
    #     if self.status in [StatusEnum.COMPLETED, StatusEnum.ABORTED]:
    #         ret["completed_at"] = utc_as_rfc_datetime(self.completed_at)
    #     if full_nodes:
    #         ret["node_statuses"] = [node_statuses.as_json() for node_statuses in self.node_statuses]
    #     elif self.node_statuses and self.status != StatusEnum.COMPLETED:
    #         current_node = self.node_statuses[-1]
    #         ret['current_node'] = current_node.as_json(summary=True)
    #
    #     return ret


class NodeStatus(Execution_Base):
    """ORM for an Node event in the database

    Attributes:
        node_id (UUID): The ID of the Node
        label (str): The label of the Node
        app_name (str): The App name for the Node
        name (str): The Node name for the Node
        result (str): The result of the Node
        status (StatusEnum): The status of the Node
        started_at (datetime): The time the Node started
        completed_at (datetime): The time the Node completed
        workflow_execution_id (UUID): The FK ID of the WorkflowStatusMessage
    """
    __tablename__ = 'node_status'
    combined_id = Column(String, primary_key=True)
    node_id = Column(UUIDType(binary=False), nullable=False)
    name = Column(String, nullable=False)
    app_name = Column(String, nullable=False)
    label = Column(String, nullable=False)
    result = Column(JSON)
    arguments = Column(String)  # TODO: refactor this to parameters to match every other node model
    status = Column(String, nullable=False)  # ToDo: revisit this and make this a real enum
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    workflow_execution_id = Column(UUIDType(binary=False),
                                   ForeignKey('workflow_status.execution_id', ondelete='CASCADE'))

    def __init__(self, combined_id, node_id, name, app_name, label, result=None, arguments=None,
                 status=StatusEnum.EXECUTING, started_at=None, completed_at=None, execution_id=None):
        self.combined_id = combined_id
        self.node_id = node_id
        self.name = name
        self.app_name = app_name
        self.label = label
        self.result = result
        self.arguments = arguments
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.execution_id = execution_id

    # def aborted(self):
    #     """Sets status to aborted"""
    #     if self.status == StatusEnum.AWAITING_DATA:
    #         self.status = StatusEnum.ABORTED
    #
    # def running(self):
    #     """Sets status to running"""
    #     self.status = StatusEnum.EXECUTING
    #
    # def awaiting_data(self):
    #     """Sets status to awaiting data"""
    #     self.status = StatusEnum.AWAITING_DATA
    #
    # def completed_success(self, data):
    #     """Sets status to completed successfully"""
    #     self.status = StatusEnum.SUCCESS
    #     self.result = json.dumps(data['result'])
    #     self.completed_at = datetime.utcnow()
    #
    # def completed_failure(self, data):
    #     """Sets status to completed unsuccessfully"""
    #     self.status = StatusEnum.FAILURE
    #     self.result = json.dumps(data['result'])
    #     self.completed_at = datetime.utcnow()
    #
    # def as_json(self, summary=False):
    #     """Gets the JSON representation of the object
    #
    #     Args:
    #         summary (bool, optional): Only get a limited JSON? Defaults to False
    #
    #     Returns:
    #         (dict): The JSON representation of the object
    #     """
    #     ret = {"execution_id": str(self.workflow_execution_id),
    #            "node_id": str(self.node_id),
    #            "label": self.label,
    #            "app_name": self.app_name,
    #            "name": self.name}
    #     if summary:
    #         return ret
    #     ret.update(
    #         {"arguments": json.loads(self.arguments) if self.arguments else [],
    #          "status": self.status.name,
    #          "started_at": utc_as_rfc_datetime(self.started_at)})
    #     if self.status in [StatusEnum.SUCCESS, StatusEnum.FAILURE]:
    #         ret["result"] = json.loads(self.result)
    #         ret["completed_at"] = utc_as_rfc_datetime(self.completed_at)
    #     return ret


class NodeStatusSchema(ExecutionBaseSchema):
    """
    Schema for NodeStatusMessage
    """
    node_id = field_for(NodeStatus, 'node_id', required=True)
    name = field_for(NodeStatus, 'name', required=True)
    app_name = field_for(NodeStatus, 'app_name', required=True)
    label = field_for(NodeStatus, 'label', required=True)
    result = field_for(NodeStatus, 'result')
    status = field_for(NodeStatus, 'status', required=True)
    started_at = field_for(NodeStatus, 'started_at')
    completed_at = field_for(NodeStatus, 'completed_at')

    class Meta:
        model = NodeStatus
        unknown = EXCLUDE


class NodeStatusSummarySchema(ExecutionBaseSchema):
    """
    Summary Schema for NodeStatusMessage
    """
    node_id = field_for(NodeStatus, 'node_id', required=True)
    name = field_for(NodeStatus, 'name', required=True)
    app_name = field_for(NodeStatus, 'app_name', required=True)
    label = field_for(NodeStatus, 'label', required=True)

    class Meta:
        model = NodeStatus
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
    node_statuses = fields.Nested(NodeStatusSchema, many=True)

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
    node_statuses = fields.Nested(NodeStatusSchema)

    class Meta:
        model = WorkflowStatus
        unknown = EXCLUDE
