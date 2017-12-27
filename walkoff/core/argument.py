import logging

from walkoff.core.helpers import InvalidArgument
from walkoff.core.representable import Representable

logger = logging.getLogger(__name__)


class Argument(Representable):
    def __init__(self, name, value=None, reference=None, selection=None):
        """Initializes an Argument object.

        Args:
            name (str): The name of the Argument.
            value (optional): The value of the Argument. Defaults to None. Value or reference must be included.
            reference (str, optional): The UID of the Action from which to grab the result. Defaults to None.
                If value is not provided, then reference must be included.
            selection (list, optional): A list of fields from which to dereference the Action result. Defaults
                to None.
        """
        if value is None and not reference:
            message = 'Input {} must have either value or reference. Input has neither'.format(name)
            logger.error(message)
            raise InvalidArgument(message)
        elif value is not None and reference:
            message = 'Input {} must have either value or reference. Input has both. Using "value"'.format(name)
            logger.warning(message)

        self.name = name
        self.value = value
        self.reference = reference if reference else None
        self.selection = selection if selection else None
        self._is_reference = True if value is None else False

    def is_ref(self):
        """Returns whether the reference field is being used, or the value field.

        Returns:
            True if the reference field is being used, False if otherwise.
        """
        return self._is_reference

    def get_value(self, accumulator):
        """Returns the value associated with this Argument, either by returning Argument.value, or using the
            accumulator to dereference the associated Action output.

        Args:
            accumulator (dict): The accumulated output from previous Actions.

        Returns:
            The value associated with this Argument.
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

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value and self.reference == other.reference and \
               self.selection == other.selection and self._is_reference == other.is_ref()
