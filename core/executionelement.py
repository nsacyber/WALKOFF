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
    def create(cls, representation, reader=JsonElementCreator):
        reader.create(representation, element_class=cls)

    def read(self, reader=None):
        if reader is None:
            reader = JsonElementReader
        return reader.read(self)
