import logging
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID

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
    _walkoff_type = Column(String(80), default=__tablename__)

    # Columns specific to WorkflowVariable model
    description = Column(String(255), default="")
    workflow_id = Column(UUID(as_uuid=True), ForeignKey('workflow.id_', ondelete='CASCADE'))

    def __init__(self, **kwargs):
        super(WorkflowVariable, self).__init__(**kwargs)
        self._walkoff_type = self.__tablename__


class WorkflowVariableSchema(BaseSchema):
    """Schema for workflow variables
    """

    class Meta:
        model = WorkflowVariable
        unknown = EXCLUDE
