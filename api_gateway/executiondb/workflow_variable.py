import logging
from uuid import UUID

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy_utils import UUIDType
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Base, VariableMixin, BaseSchema

logger = logging.getLogger(__name__)


class WorkflowVariable(VariableMixin, Base):
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
    description = Column(String(255), default="")
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))


class WorkflowVariableSchema(BaseSchema):
    """Schema for workflow variables
    """
    # # From IDMixin
    # id_ = field_for(WorkflowVariable, 'id_', required=True)
    #
    # # From VariableMixin
    # name = field_for(WorkflowVariable, 'name', required=True)
    # value = field_for(WorkflowVariable, 'value', required=True)
    # description = field_for(WorkflowVariable, 'description')

    class Meta:
        model = WorkflowVariable
        unknown = EXCLUDE
