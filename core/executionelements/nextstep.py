import logging

from core.case.callbacks import data_sent
from core.executionelements.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


class NextStep(ExecutionElement):
    def __init__(self, status='Success', name='', flags=None, uid=None):
        """Initializes a new NextStep object.
        
        Args:
            name (str, optional): The name of the NextStep object. Defaults to an empty string.
            flags (list[Flag], optional): A list of Flag objects for the NextStep object. Defaults to None.
            uid (str, optional): A universally unique identifier for this object.
            Created from uuid.uuid4() in Python
        """
        ExecutionElement.__init__(self, uid)
        self.name = name
        self.status = status
        self.flags = flags if flags is not None else []

    def __eq__(self, other):
        return self.name == other.name and self.status == other.status and set(self.flags) == set(other.flags)

    def execute(self, data_in, accumulator):
        if data_in is not None and data_in.status == self.status:
            if all(flag.execute(data_in=data_in.result, accumulator=accumulator) for flag in self.flags):
                data_sent.send(self, callback_name="Next Step Taken", object_type="NextStep")
                logger.debug('NextStep is valid for input {0}'.format(data_in))

                return self.name
            else:
                logger.debug('NextStep is not valid for input {0}'.format(data_in))
                data_sent.send(self, callback_name="Next Step Not Taken", object_type="NextStep")
                return None
        else:
            return None
