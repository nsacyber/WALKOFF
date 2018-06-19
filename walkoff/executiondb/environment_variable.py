import logging

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy_utils import UUIDType
from walkoff.executiondb import Execution_Base

logger = logging.getLogger(__name__)


class EnvironmentVariable(Execution_Base):
    __tablename__ = 'environment_variable'
    id = Column(UUIDType(binary=False), primary_key=True)
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id'))
    name = Column(String(80), nullable=False)
    value = Column(String(80), nullable=False)
    type = Column(String(80), nullable=False)

    def __init__(self, name, value, type):
        self.name = name
        self.value = value
        self.type = type
