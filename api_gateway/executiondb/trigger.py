import logging

from sqlalchemy import Column, String, ForeignKey, orm, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from marshmallow import fields, EXCLUDE
from marshmallow_sqlalchemy import field_for

from api_gateway.executiondb.schemas import ExecutionElementBaseSchema
from api_gateway.executiondb.position import PositionSchema
from api_gateway.appgateway.apiutil import InvalidParameter
from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


class Trigger(ExecutionElement, Execution_Base):
    __tablename__ = 'trigger'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))

    name = Column(String(255), nullable=False)
    trigger = Column(String(512), nullable=False)
    position = relationship('Position', uselist=False, cascade='all, delete-orphan', passive_deletes=True)

    def __init__(self, name, trigger, position=None, id_=None, errors=None):
        """Initializes a new Trigger object. A Trigger is used to trigger input into a workflow.

        Args:
            name (str): The name associated with this trigger
            id_ (str|UUID, optional): Optional UUID to pass into the Trigger. Must be UUID object or valid UUID string.
                Defaults to None.
            trigger (str): Python code snippet representing the trigger condition to be checked
            position (Position, optional): Position object for the Action. Defaults to None.

        """
        ExecutionElement.__init__(self, id_, errors)
        self.name = name
        self.trigger = trigger
        self.position = position
        self.validate()

    # TODO: Implement validation of conditional against asteval library
    def validate(self):
        """Validates the object"""
        errors = []
        try:
            pass
        except InvalidParameter as e:
            errors.extend(e.errors)
        self.errors = errors

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Condition being loaded from database"""
        pass


@event.listens_for(Trigger, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()



class TriggerSchema(ExecutionElementBaseSchema):
    """Schema for triggers
    """

    name = field_for(Trigger, 'name', required=True)
    trigger = field_for(Trigger, 'trigger', required=True)
    position = fields.Nested(PositionSchema())

    class Meta:
        model = Trigger
        unknown = EXCLUDE

