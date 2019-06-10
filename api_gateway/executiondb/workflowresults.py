from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref

from marshmallow import fields, EXCLUDE
from marshmallow_enum import EnumField

from common.message_types import StatusEnum
from api_gateway.executiondb import Base, BaseSchema


class WorkflowStatus(Base):
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

    # Columns common to Status messages
    name = Column(String(80), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False)
    started_at = Column(String, default="")
    completed_at = Column(String, default="")

    # Columns specific to WorkflowStatus model
    execution_id = Column(UUID(as_uuid=True), primary_key=True)
    workflow_id = Column(UUID(as_uuid=True))
    user = Column(String, default="")
    # TODO: change these on the db model to be keyed by ID (use an association proxy)
    node_statuses = relationship('NodeStatus', backref=backref("execution_id"), passive_deletes=True,
                                 cascade='all, delete-orphan')


class NodeStatus(Base):
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

    # Columns common to Status messages
    name = Column(String(80), nullable=False)
    status = Column(Enum(StatusEnum), nullable=False)
    started_at = Column(String, default="")
    completed_at = Column(String, default="")

    # Columns specific to NodeStatus model
    combined_id = Column(String, primary_key=True)
    node_id = Column(UUID(as_uuid=True), nullable=False)
    app_name = Column(String, nullable=False)
    label = Column(String, nullable=False)
    result = Column(JSON, default=None)
    parameters = Column(JSON, default=None)
    #arguments = Column(String)  # TODO: refactor this to parameters to match every other node model

    workflow_execution_id = Column(UUID(as_uuid=True),
                                   ForeignKey('workflow_status.execution_id', ondelete='CASCADE'))


class NodeStatusSchema(BaseSchema):
    """
    Schema for NodeStatusMessage
    """

    status = EnumField(StatusEnum)

    class Meta:
        model = NodeStatus
        unknown = EXCLUDE


class WorkflowStatusSchema(BaseSchema):
    """
    Schema for WorkflowStatusMessage
    """

    status = EnumField(StatusEnum)
    node_statuses = fields.Nested(NodeStatusSchema, many=True)

    class Meta:
        model = WorkflowStatus
        unknown = EXCLUDE
