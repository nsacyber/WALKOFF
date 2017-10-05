import uuid
from core.jsonelementcreator import JsonElementCreator
from core.jsonelementreader import JsonElementReader


class ExecutionElement(object):
    def __init__(self, uid=None):
        """Initializes a new ExecutionElement object. This is the parent class.
        
        Args:
            name (str, optional): The name of the ExecutionElement. Defaults to an empty string.
            uid (str, optional): The UID of this ExecutionElement. Constructed from a UUID4 hex string
        """
        self.uid = uuid.uuid4().hex if uid is None else uid

    @classmethod
    def create(cls, representation, creator=JsonElementCreator):
        return creator.create(representation, element_class=cls)

    def read(self, reader=None):
        if reader is None:
            reader = JsonElementReader
        return reader.read(self)

    def __repr__(self):
        representation = self.read()
        uid = representation.pop('uid', None)
        out = '<{0} at {1} : uid={2}'.format(self.__class__.__name__, hex(id(self)), uid)
        for key, value in representation.items():
            if (isinstance(value, list)
                    and all(isinstance(list_value, dict) and 'uid' in list_value for list_value in value)):
                out += ', {0}={1}'.format(key, [list_value['uid'] for list_value in value])
            else:
                out += ', {0}={1}'.format(key, value)
        out += '>'
        return out

