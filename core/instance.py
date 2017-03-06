from core.helpers import import_app_main

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

    @staticmethod
    def create(app_name, device_name):
        imported = import_app_main(app_name)
        if imported:
            return Instance(instance=getattr(imported, "Main")(name=app_name, device=device_name), state=OK)

    def __call__(self):
        return self.instance

    def shutdown(self):
        self.instance.shutdown()
        self.state = 0

    def __repr__(self):
        output = {'instance': str(self.instance),
                  'state': str(self.state)}
        return str(output)
