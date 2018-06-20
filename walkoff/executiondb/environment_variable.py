import logging
from uuid import uuid4

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy_utils import UUIDType
from walkoff.executiondb import Execution_Base

logger = logging.getLogger(__name__)


class EnvironmentVariable(Execution_Base):
    __tablename__ = 'environment_variable'
    id = Column(UUIDType(binary=False), primary_key=True, nullable=False, default=uuid4)
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id'))
    name = Column(String(80), nullable=False)
    value = Column(String(80), nullable=False)

    def __init__(self, name, value, id=None):
        if id:
            self.id = id
        self.name = name
        self.value = value
