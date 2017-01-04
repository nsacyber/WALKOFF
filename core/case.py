import uuid

class Case(object):
    def __init__(self, id="", history=[]):
        self.id = id
        self.uid = uuid.uuid4()
        self.history = history



