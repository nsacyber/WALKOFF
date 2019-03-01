import logging
from uuid import uuid4, UUID

from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType

from api_gateway.executiondb import Execution_Base

logger = logging.getLogger(__name__)


class GlobalVariable(Execution_Base):
    """SQLAlchemy ORM class for Global, which are variables that can be dynamically loaded into workflow
       execution

    Attributes:
        _id (UUID): The ID of the object
        name (str): The name of the environment variable
        value (any): The value of the object
        description (str): A description of the object

    """
    __tablename__ = 'global_variable'
    _id = Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)
    name = Column(String(80))
    value = Column(String(80), nullable=False)
    description = Column(String(255))

    def __init__(self, value, _id=None, name=None, description=None):
        if _id:
            if not isinstance(_id, UUID):
                self._id = UUID(_id)
            else:
                self._id = _id
        self.name = name
        self.value = value
        self.description = description
