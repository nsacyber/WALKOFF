import logging
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import UUIDType
from marshmallow import EXCLUDE

from api_gateway.executiondb import Base, BaseSchema

logger = logging.getLogger(__name__)


class WorkflowVariable(Base):
    """SQLAlchemy ORM class for WorkflowVariable, which are variables that can be dynamically loaded into workflow
       execution

    Attributes:
        id_ (UUID): The ID of the object
        workflow_id (UUID): The corresponding workflow ID that this environment variable relates to
        name (str): The name of the environment variable
        value (any): The value of the object
        description (str): A description of the object

    """
    __tablename__ = 'workflow_variable'

    # Columns common to all DB models
    id_ = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    # Columns common to all Variable models
    name = Column(String(80), nullable=False)
    value = Column(JSON)

    # Columns specific to WorkflowVariable model
    description = Column(String(255), default="")
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))


class WorkflowVariableSchema(BaseSchema):
    """Schema for workflow variables
    """

    class Meta:
        model = WorkflowVariable
        unknown = EXCLUDE
