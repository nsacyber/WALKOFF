import logging

from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType

logger = logging.getLogger(__name__)


class EnvironmentVariable(object):
    __tablename__ = 'environment_variable'
    id = Column(UUIDType(binary=False))
    name = Column(String(80), nullable=False)
    value = Column(String(80), nullable=False)
    type = Column(String(80), nullable=False)

    def __init__(self, name, value, type):
        self.name = name
        self.value = value
        self.type = type
