import logging
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.flag import Flag
import uuid

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
        ExecutionElement.__init__(self, name, uid)
        self.status = status
        self.flags = flags if flags is not None else []

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
        output = {'uid': self.uid,
                  'flags': [flag.as_json() for flag in self.flags],
                  'status': self.status,
                  'name': self.name}
        return str(output)

    def as_json(self):
        """Gets the JSON representation of a NextStep object.

        Returns:
            The JSON representation of a NextStep object.
        """
        return {"uid": self.uid,
                "flags": [flag.as_json() for flag in self.flags],
                "status": self.status,
                "name": str(self.name) if self.name else ''}

    @staticmethod
    def from_json(json):
        """Forms a NextStep object from the provided JSON object.
        
        Args:
            json (JSON object): The JSON object to convert from.
            
        Returns:
            The NextStep object parsed from the JSON object.
        """
        name = json['name'] if 'name' in json else ''
        status = json['status'] if 'status' in json else 'Success'
        uid = json['uid'] if 'uid' in json else uuid.uuid4().hex
        next_step = NextStep(name=name, status=status, uid=uid)
        if json['flags']:
            next_step.flags = [Flag.from_json(flag) for flag in json['flags']]
        return next_step
