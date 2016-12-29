
"""
States
"""
OK = 1
SHUTDOWN = 0
ERROR = -1

class Instance(object):
    def __init__(self, instance=None, state=1):
        self.instance = instance
        self.state = state

    def __call__(self):
        return self.instance

    def shutdown(self):
        self.instance.shutdown()
        self.state = 0

    def __repr__(self):
        output = dict()
        output["instance"] = str(self.instance)
        output["state"] = str(self.state)
        return str(output)