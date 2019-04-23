import logging

from sqlalchemy import Column, String, ForeignKey, JSON, orm, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE

from api_gateway.executiondb import IDMixin, Base, BaseSchema

logger = logging.getLogger(__name__)


class Trigger(IDMixin, Base):
    __tablename__ = 'trigger'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))

    name = Column(String(255), nullable=False)
    # trigger = Column(String(512), nullable=False)
    position = Column(JSON, default={"x": 0, "y": 0})


class TriggerSchema(BaseSchema):
    """Schema for triggers
    """

    class Meta:
        model = Trigger
        unknown = EXCLUDE
