import logging
from uuid import uuid4, UUID

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy_utils import UUIDType

from walkoff.executiondb import Execution_Base

logger = logging.getLogger(__name__)


class EnvironmentVariable(Execution_Base):
    """SQLAlchemy ORM class for EnvironmentVariables, which are variables that can be dynamically loaded into workflow
       execution

    Attributes:
        id (UUID): The ID of the object
        workflow_id (UUID): The corresponding workflow ID that this environment variable relates to
        name (str): The name of the environment variable
        value (any): The value of the object
        description (str): A description of the object

    """
    __tablename__ = 'environment_variable'
    id = Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id', ondelete='CASCADE'))
    name = Column(String(80))
    value = Column(String(80), nullable=False)
    description = Column(String(255))

    def __init__(self, value, id=None, name=None, description=None):
        if id:
            if not isinstance(id, UUID):
                self.id = UUID(id)
            else:
                self.id = id
        self.name = name
        self.value = value
        self.description = description
