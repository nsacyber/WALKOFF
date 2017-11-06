import logging
from core.helpers import InvalidInput

logger = logging.getLogger(__name__)


class Argument:
    def __init__(self, name, value=None, reference='', selection=None):
        if not value and not reference:
            message = 'Input {} must have either value or reference. Input has neither'.format(name)
            logger.error(message)
            raise InvalidInput(message)
        elif value and reference:
            message = 'Input {} must have either value or reference. Input has both. Using "value"'.format(name)
            logger.warning(message)

        self.name = name
        self.value = value
        self.reference = reference
        self.selection = selection

    def get_value(self, accumulator):
        if self.value is not None:
            return self.value

        step_output = self.__get_step_from_reference(accumulator)
        if not self.selection:
            return step_output

        for index in self.selection:
            try:
                if isinstance(step_output, dict):
                    step_output = step_output[index]
                elif isinstance(step_output, list):
                    step_output = step_output[int(index)]
                else:
                    raise ValueError
            except (KeyError, ValueError, IndexError):
                raise InvalidInput('Selector {0} is invalid for reference {1}'.format(
                    self.selection, self.reference))
        return step_output

    def __get_step_from_reference(self, accumulator):
        if self.reference in accumulator:
            return accumulator[self.reference]
        else:
            message = ('Referenced step {} '
                       'has not been executed'.format(self.reference))
            raise InvalidInput(message)
