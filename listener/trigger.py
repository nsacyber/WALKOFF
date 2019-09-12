class Trigger():
    def __init__(self, id, event_type, parent, prefix, suffix, workflow):
        self.id = id
        self.event_type = event_type
        self.parent = parent
        self.prefix = prefix
        self.suffix = suffix
        self.workflow = workflow
        self.running = False
        self.runtime = None

    def __eq__(self, other):
        if not isinstance(other, Trigger):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash((self.id))