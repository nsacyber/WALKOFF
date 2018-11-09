import logging

from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy_utils import UUIDType

from walkoff.executiondb import Execution_Base

logger = logging.getLogger(__name__)


class Position(Execution_Base):
    __tablename__ = 'position'
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(UUIDType(binary=False), ForeignKey('action.id', ondelete='CASCADE'))
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)

    def __init__(self, x, y):
        """Initializes a new Position object. An Action has a Position object.

        Args:
            x (float): The X coordinate of the Action.
            y (float): The Y coordinate of the Action.
        """
        self.x = x
        self.y = y
