import logging

from sqlalchemy import Column, Integer, ForeignKey, String, orm, event
from sqlalchemy_utils import UUIDType, JSONType, ScalarListType

from walkoff.executiondb import Execution_Base
from walkoff.executiondb.validatable import Validatable
from walkoff.appgateway.apiutil import InvalidArgument

logger = logging.getLogger(__name__)


class Argument(Execution_Base, Validatable):
    __tablename__ = 'argument'
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(UUIDType(binary=False), ForeignKey('action.id'))
    action_device_id = Column(UUIDType(binary=False), ForeignKey('action.id'))
    condition_id = Column(UUIDType(binary=False), ForeignKey('condition.id'))
    transform_id = Column(UUIDType(binary=False), ForeignKey('transform.id'))
    name = Column(String(255), nullable=False)
    value = Column(JSONType)
    reference = Column(UUIDType(binary=False))
    selection = Column(ScalarListType())
    errors = Column(ScalarListType())

    def __init__(self, name, value=None, reference=None, selection=None):
        """Initializes an Argument object.

        Args:
            name (str): The name of the Argument.
            value (any, optional): The value of the Argument. Defaults to None. Value or reference must be included.
            reference (int, optional): The ID of the Action from which to grab the result. Defaults to None.
                If value is not provided, then reference must be included.
            selection (list, optional): A list of fields from which to dereference the Action result. Defaults
                to None. Must be used in conjunction with reference.
        """
        self.name = name
        self.value = value
        self._is_reference = True if value is None else False
        self.reference = reference
        self.selection = selection
        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Argument being loaded from database"""
        self._is_reference = True if self.value is None else False

    def validate(self):
        """Validates the object"""
        if self.value is None and not self.reference:
            message = 'Input {} must have either value or reference. Input has neither'.format(self.name)
            logger.error(message)
            self.errors = [message]
        elif self.value is not None and self.reference:
            message = 'Input {} must have either value or reference. Input has both. Using "value"'.format(self.name)
            logger.warning(message)
            self.reference = None

    def update_value_reference(self, value, reference):
        """Helper function to ensure that either reference or value is selected and the other is None

        Args:
            value (any): The value to set. Can be None
            reference (int): The reference to set. Can be none
        """
        if value is not None and (self.value != value or self.reference):
            self.value = value
            self.reference = None
            self.selection = []
        elif reference:
            self.reference = reference
            self.value = None
            self._is_reference = True

    @property
    def is_ref(self):
        """Returns whether the reference field is being used, or the value field.

        Returns:
            (bool): True if the reference field is being used, False if otherwise.
        """
        return self._is_reference

    def get_value(self, accumulator):
        """Returns the value associated with this Argument, either by returning Argument.value, or using the
            accumulator to dereference the associated Action output.

        Args:
            accumulator (dict): The accumulated output from previous Actions.

        Returns:
            (any): The value associated with this Argument.
        """
        if self.value is not None:
            return self.value

        if accumulator:
            action_output = self._get_action_from_reference(accumulator)
            if not self.selection:
                return action_output

            return self._select(action_output)
        else:
            return self.reference

    def _get_action_from_reference(self, accumulator):
        try:
            return accumulator[self.reference]
        except KeyError:
            message = ('Referenced action {} '
                       'has not been executed'.format(self.reference))
            raise InvalidArgument(message)

    def _select(self, input_):
        try:
            for selection in self.selection:
                input_ = Argument._get_next_selection(input_, selection)
            return input_

        except (KeyError, ValueError, IndexError):
            raise InvalidArgument('Selector {0} is invalid for reference {1}'.format(
                self.selection, self.reference))

    @staticmethod
    def _get_next_selection(input_, selection):
        if isinstance(input_, dict):
            return input_[selection]
        elif isinstance(input_, list):
            return input_[int(selection)]
        else:
            raise ValueError

    @classmethod
    def create_device_argument(cls, value=None, reference=None, selection=None):
        return cls(name='__device__', value=value, reference=reference, selection=selection)

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value and self.reference == other.reference and \
               self.selection == other.selection and self._is_reference == other.is_ref

    def __hash__(self):
        return hash(self.id)


@event.listens_for(Argument, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()
