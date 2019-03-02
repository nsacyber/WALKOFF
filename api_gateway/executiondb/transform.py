import logging

from sqlalchemy import Column, String, ForeignKey, orm, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from api_gateway.appgateway.apiutil import InvalidParameter
from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


class Transform(ExecutionElement, Execution_Base):
    __tablename__ = 'transform'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id_', ondelete='CASCADE'))

    name = Column(String(255), nullable=False)
    transform = Column(String(80), nullable=False)
    parameter = relationship('Parameter', cascade='all, delete, delete-orphan', passive_deletes=True)
    position = relationship('Position', uselist=False, cascade='all, delete-orphan', passive_deletes=True)

    children = ('argument',)

    def __init__(self, name, transform, position=None, id_=None, parameter=None, errors=None):
        """Initializes a new Transform object. A Transform is used to transform input into a workflow.

        Args:
            name (str): The app name associated with this transform
            id_ (str|UUID, optional): Optional UUID to pass into the Transform. Must be UUID object or valid UUID string.
                Defaults to None.
            position (Position, optional): Position object for the Action. Defaults to None.
            transform (str): The name of the transform function to be applied
            parameter (str): The optional parameter to feed into the transform function i.e index or key
        """
        ExecutionElement.__init__(self, id_, errors)
        self.name = name
        self.transform = transform
        self.position = position
        self.parameter = parameter
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


@event.listens_for(Transform, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()
