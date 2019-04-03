import logging

from sqlalchemy import Column, String, ForeignKey, orm, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb.schemas import ExecutionElementBaseSchema
from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.executionelement import ExecutionElement
from api_gateway.executiondb.position import PositionSchema

logger = logging.getLogger(__name__)


class Condition(ExecutionElement, Execution_Base):
    __tablename__ = 'condition'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))

    name = Column(String(255), nullable=False)
    conditional = Column(String(512), nullable=False)
    position = relationship('Position', uselist=False, cascade='all, delete-orphan', passive_deletes=True)

    def __init__(self, name, conditional, id_=None, position=None, errors=None):
        """Initializes a new Condition object.

        Args:
            name (str): The name of this condition
            position (Position, optional): Position object for the Action. Defaults to None.
            id_ (str|UUID, optional): Optional UUID to for the Condition. Must be UUID object or valid UUID string.
                Defaults to None.
        """
        ExecutionElement.__init__(self, id_, errors)

        self.name = name
        self.conditional = conditional
        self.position = position

        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Condition being loaded from database"""
        pass

    # TODO: Implement validation of conditional against asteval library
    def validate(self):
        """Validates the object"""
        errors = []
        pass


@event.listens_for(Condition, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()


class ConditionSchema(ExecutionElementBaseSchema):
    """Schema for conditions
    """

    name = field_for(Condition, 'name', required=True)
    conditional = field_for(Condition, 'conditional', required=True)
    position = fields.Nested(PositionSchema())

    class Meta:
        model = Condition
        unknown = EXCLUDE


