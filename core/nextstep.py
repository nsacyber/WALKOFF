
import logging
from core.case import callbacks
from core.data.nextStep import NextStepData


logger = logging.getLogger(__name__)


class NextStep(NextStepData):
    def __init__(self, xml=None, status='Success', name='', parent_name='', flags=None, ancestry=None):
        """Initializes a new NextStep object.
        
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            name (str, optional): The name of the NextStep object. Defaults to an empty string.
            flags (list[Flag], optional): A list of Flag objects for the NextStep object. Defaults to None.
            ancestry (list[str], optional): The ancestry for the NextStep object. Defaults to None.
        """
        NextStepData.__init__(self, xml, status, name, parent_name, flags, ancestry)

    def __eq__(self, other):
        return self.name == other.name and self.status == other.status and set(self.flags) == set(other.flags)

    def __call__(self, data_in, accumulator):
        if data_in is not None and data_in.status == self.status:
            if all(flag(data_in=data_in.result, accumulator=accumulator) for flag in self.flags):
                callbacks.NextStepTaken.send(self)
                logger.debug('NextStep is valid for input {0}'.format(data_in))
                return self.name
            else:
                logger.debug('NextStep is not valid for input {0}'.format(data_in))
                callbacks.NextStepNotTaken.send(self)
                return None
        else:
            return None

    def __repr__(self):
        output = {'flags': [flag.as_json() for flag in self.flags],
                  'status': self.status,
                  'name': self.name}
        return str(output)






