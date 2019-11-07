from typing import List, Dict, Union
from uuid import UUID

from pydantic import BaseModel

from api.server.db import IDBaseModel
from api.server.db.parameter import ParameterModel
from api.server.db.workflow_variable import WorkflowVariableModel
from api.server.utils.helpers import JSONOrString
from common.message_types import StatusEnum


class UpdateMessage(BaseModel):
    execution_id: UUID
    workflow_id: UUID
    message: str
    type: str


class NodeStatus(BaseModel):
    name: str
    status: StatusEnum
    started_at: str = ""
    completed_at: str = ""
    combined_id: str = None
    node_id: UUID
    app_name: str
    label: str
    result: JSONOrString = None
    parameters: dict = {}
    execution_id: UUID


class WorkflowStatus(IDBaseModel):
    name: str
    status: StatusEnum
    started_at: str = ""
    completed_at: str = ""
    execution_id: UUID = None
    workflow_id: UUID = None
    user: str = ""
    node_statuses: Union[Dict[str, NodeStatus], List[NodeStatus]] = {}
    app_name: str = ""
    action_name: str = ""
    label: str = ""
    _id_field: str = "execution_id"

    def to_response(self):
        self.node_statuses = [node_status for node_status in list(self.node_statuses.values())]


class ExecuteWorkflow(BaseModel):
    workflow_id: UUID
    execution_id: UUID = None
    start: UUID = None
    parameters: List[ParameterModel] = []
    workflow_variables: List[WorkflowVariableModel] = []


class ControlWorkflow(BaseModel):
    status: str  # ToDo: enum this
    trigger_id: UUID = None
    trigger_data: dict = None

# class WorkflowStatus(Base):
#     """ORM for a Status of a Workflow in the database
#
#     Attributes:
#         execution_id (UUID): Execution ID of the Workflow
#         workflow_id (UUID): ID of the Workflow
#         name (str): Name of the Workflow
#         status (str): Status of the Workflow
#         started_at (datetime): Time the Workflow started
#         completed_at (datetime): Time the Workflow ended
#         user (str): The user who initially executed this workflow
#         node_status (list[NodeStatus]): A list of NodeStatusMessage objects for this WorkflowStatusMessage
#         current_app
#     """
#     __tablename__ = 'workflow_status'
#
#     # Columns common to Status messages
#     name = Column(String(80), nullable=False)
#     status = Column(Enum(StatusEnum), nullable=False)
#     started_at = Column(String, default="")
#     completed_at = Column(String, default="")
#
#     # Columns specific to WorkflowStatus model
#     execution_id = Column(UUID(as_uuid=True), primary_key=True)
#     workflow_id = Column(UUID(as_uuid=True))
#     user = Column(String, default="")
#     # TODO: change these on the db model to be keyed by ID (use an association proxy)
#     node_status = relationship('NodeStatus', backref=backref("execution_id"), passive_deletes=True,
#                                  cascade='all, delete-orphan')
#     app_name = Column(String, default="")
#     action_name = Column(String, default="")
#     label = Column(String, default="")
#
#
# class NodeStatus(Base):
#     """ORM for an Node event in the database
#
#     Attributes:
#         node_id (UUID): The ID of the Node
#         label (str): The label of the Node
#         app_name (str): The App name for the Node
#         name (str): The Node name for the Node
#         result (str): The result of the Node
#         status (StatusEnum): The status of the Node
#         started_at (datetime): The time the Node started
#         completed_at (datetime): The time the Node completed
#         workflow_execution_id (UUID): The FK ID of the WorkflowStatusMessage
#     """
#     __tablename__ = 'node_status'
#
#     # Columns common to Status messages
#     name = Column(String(80), nullable=False)
#     status = Column(Enum(StatusEnum), nullable=False)
#     started_at = Column(String, default="")
#     completed_at = Column(String, default="")
#
#     # Columns specific to NodeStatus model
#     combined_id = Column(String, primary_key=True)
#     node_id = Column(UUID(as_uuid=True), nullable=False)
#     app_name = Column(String, nullable=False)
#     label = Column(String, nullable=False)
#     result = Column(JSON, default=None)
#     parameters = Column(JSON, default=None)
#
#     workflow_execution_id = Column(UUID(as_uuid=True),
#                                    ForeignKey('workflow_status.execution_id', ondelete='CASCADE'))

#
# class NodeStatusSchema(BaseSchema):
#     """
#     Schema for NodeStatusMessage
#     """
#
#     status = EnumField(StatusEnum)
#
#     class Meta:
#         model = NodeStatus
#         unknown = EXCLUDE
#
#
# class WorkflowStatusSchema(BaseSchema):
#     """
#     Schema for WorkflowStatusMessage
#     """
#
#     status = EnumField(StatusEnum)
#     node_status = fields.Nested(NodeStatusSchema, many=True)
#
#     class Meta:
#         model = WorkflowStatus
#         unknown = EXCLUDE
