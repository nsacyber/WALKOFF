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
            Created from uuid.uuid4().hex in Python
        """
        ExecutionElement.__init__(self, uid)
        self.name = name
        self.status = status
        self.flags = flags if flags is not None else []

    def __send_callback(self, callback_name):
        data = dict()
        data['callback_name'] = callback_name
        data['sender'] = {}
        data['sender']['name'] = self.name
        data['sender']['id'] = self.name
        data['sender']['uid'] = self.uid
        data_sent.send(None, data=data)

    def __eq__(self, other):
        return self.name == other.name and self.status == other.status and set(self.flags) == set(other.flags)

    def __call__(self, data_in, accumulator):
        if data_in is not None and data_in.status == self.status:
            if all(flag(data_in=data_in.result, accumulator=accumulator) for flag in self.flags):
                self.__send_callback("Next Step Taken")
                logger.debug('NextStep is valid for input {0}'.format(data_in))

                return self.name
            else:
                logger.debug('NextStep is not valid for input {0}'.format(data_in))
                self.__send_callback("Next Step Not Taken")
                return None
        else:
            return None
