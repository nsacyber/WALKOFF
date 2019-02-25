import logging

from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy_utils import UUIDType

from api_gateway.executiondb import Execution_Base

logger = logging.getLogger(__name__)


class Position(Execution_Base):
    __tablename__ = 'position'
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(UUIDType(binary=False), ForeignKey('action._id', ondelete='CASCADE'))
    condition_id = Column(UUIDType(binary=False), ForeignKey('condition._id', ondelete='CASCADE'))
    transform_id = Column(UUIDType(binary=False), ForeignKey('transform._id', ondelete='CASCADE'))
    trigger_id = Column(UUIDType(binary=False), ForeignKey('trigger._id', ondelete='CASCADE'))

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
