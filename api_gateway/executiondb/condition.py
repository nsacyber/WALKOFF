import logging

from sqlalchemy import Column, String, ForeignKey, JSON, event
from sqlalchemy_utils import UUIDType
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb import Base, ValidatableMixin, BaseSchema

logger = logging.getLogger(__name__)


class Condition(ValidatableMixin, Base):
    __tablename__ = 'condition'

    name = Column(String(255), nullable=False)
    conditional = Column(String(512), nullable=False)
    position = Column(JSON, default={"x": 0, "y": 0})

    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))

    def __init__(self, **kwargs):
        super(Condition, self).__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validates the object"""
        # TODO: Implement validation of conditional against asteval library
        pass


@event.listens_for(Condition, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()


class ConditionSchema(BaseSchema):
    """Schema for conditions
    """
    class Meta:
        model = Condition
        unknown = EXCLUDE
        dump_only = ("errors", "is_valid")

