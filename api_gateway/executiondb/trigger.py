import logging

from sqlalchemy import Column, String, ForeignKey, JSON, orm, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE

from api_gateway.executiondb import NodeMixin, Base, BaseSchema

logger = logging.getLogger(__name__)


class Trigger(NodeMixin, Base):
    __tablename__ = 'trigger'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))

    # trigger = Column(String(512), nullable=False)

    def __init__(self, **kwargs):
        super(Trigger, self).__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validates the object"""
        # TODO: Implement validation of transform against asteval library if/when advanced transforms are implemented
        self.errors = []


class TriggerSchema(BaseSchema):
    """Schema for triggers
    """

    class Meta:
        model = Trigger
        unknown = EXCLUDE
