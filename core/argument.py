import logging
from core.helpers import InvalidInput

logger = logging.getLogger(__name__)


class Argument:
    def __init__(self, name, value=None, reference='', selection=None):
        if not value and not reference:
            logger.error("Must have either value or reference")
        if value and reference:
            logger.error("Must have etither value or reference")

        self.name = name
        if value:
            self.value = value
        elif reference:
            self.reference = reference
            if selection:
                self.selection = selection

    def get_value(self, accumulator):
        if self.value:
            return self.value
        elif self.reference:
            if not self.selection:
                return self.__get_step_from_reference(accumulator)
            else:
                step_output = self.__get_step_from_reference(accumulator)
            for index in self.selection:
                try:
                    if isinstance(step_output, dict):
                        step_output = step_output[index]
                    elif isinstance(step_output, list):
                        step_output = step_output[int(index)]
                except (KeyError, ValueError):
                    raise InvalidInput
            return step_output

    def __get_step_from_reference(self, accumulator):
        if self.reference in accumulator:
            return accumulator[self.reference]
        else:
            message = ('Referenced step {} '
                       'has not been executed'.format(self.reference))
            raise InvalidInput(message)
