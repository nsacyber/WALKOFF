import logging

from core.representable import Representable
from core.helpers import InvalidArgument

logger = logging.getLogger(__name__)


class Argument(Representable):
    def __init__(self, name, value=None, reference=None, selection=None):
        if not value and not reference:
            message = 'Input {} must have either value or reference. Input has neither'.format(name)
            logger.error(message)
            raise InvalidArgument(message)
        elif value and reference:
            message = 'Input {} must have either value or reference. Input has both. Using "value"'.format(name)
            logger.warning(message)

        self.name = name
        self.value = value
        self.reference = reference
        self.selection = selection
        self._is_reference = True if value is None else False

    def is_ref(self):
        return self._is_reference

    def get_value(self, accumulator):
        if self.value is not None:
            return self.value

        if accumulator:
            step_output = self._get_step_from_reference(accumulator)
            if not self.selection:
                return step_output

            return self._select(step_output)
        else:
            return self.reference

    def _get_step_from_reference(self, accumulator):
        try:
            return accumulator[self.reference]
        except KeyError:
            message = ('Referenced step {} '
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
               self.selection == other.selection and self._is_reference == other._is_reference
