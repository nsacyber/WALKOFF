import logging

from sqlalchemy import Column, Integer, ForeignKey, String, orm, event
from sqlalchemy_utils import UUIDType, JSONType, ScalarListType

from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.validatable import Validatable

logger = logging.getLogger(__name__)


class Parameter(Execution_Base, Validatable):
    __tablename__ = 'parameter'
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(UUIDType(binary=False), ForeignKey('action.id_', ondelete='CASCADE'))
    transform_id = Column(UUIDType(binary=False), ForeignKey('transform.id_', ondelete='CASCADE'))
    name = Column(String(255), nullable=False)
    variant = Column(String(255), nullable=False)
    value = Column(JSONType)
    reference = Column(UUIDType(binary=False))
    errors = Column(ScalarListType())

    def __init__(self, name, variant, value=None, reference=None):
        """Initializes an Parameter object.

        Args:
            name (str): The name of the Parameter.
            value (any, optional): The value of the Parameter. Defaults to None. Value or reference must be included.
            variant (str): string corresponding to a ParameterVariant. Denotes static value, action output, global, etc.
            reference (int, optional): The ID of the Action, global, or WorkflowVariable from which to grab the result.
        """
        self.name = name
        self.variant = variant
        self.value = value
        self.reference = reference
        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Parameter being loaded from database"""
        pass

    def validate(self):
        """Validates the object"""
        self.errors = []
        if self.value is None and not self.reference:
            message = 'Input {} must have either value or reference. Input has neither'.format(self.name)
            logger.error(message)
            self.errors = [message]
        elif self.value is not None and self.reference:
            message = 'Input {} must have either value or reference. Input has both. Using "value"'.format(self.name)
            logger.warning(message)
            self.reference = None

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value and self.reference == other.reference \
               and self.variant == other.variant

    def __hash__(self):
        return hash(self.id)


@event.listens_for(Parameter, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()
