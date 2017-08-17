import uuid


class ExecutionElement(object):
    def __init__(self, name='', uid=None):
        """Initializes a new ExecutionElement object. This is the parent class.
        
        Args:
            name (str, optional): The name of the ExecutionElement. Defaults to an empty string.
            uid (str, optional): The UID of this ExecutionElement. Constructed from a UUID4 hex string
        """
        self.name = name
        self.uid = uuid.uuid4().hex if uid is None else uid

    def as_json(self):
        raise NotImplementedError('as_json has not been implemented')
