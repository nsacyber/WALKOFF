import logging
from core.helpers import import_app_main

logger = logging.getLogger(__name__)

"""
States
"""
OK = 1
SHUTDOWN = 0
ERROR = -1


class Instance(object):
    def __init__(self, instance=None, state=1):
        """Initializes a new Instance of an App.
        
        Args:
            instance (Class): This is an instance of an App's module.
            state (int, optional): The state of the Instance. 1 is OK, 0 is SHUTDOWN, and -1 is ERROR. Defaults to OK.
        """
        self.instance = instance
        self.state = state

    @staticmethod
    def create(app_name, device_name):
        """Creates a new Instance object from an app name and a device name.
        
        Args:
            app_name (str): The name of the app from which to import the main module.
            device_name (str): A device pertaining to the App.
            
        Returns:
            A new Instance object.
        """
        imported = import_app_main(app_name)
        if imported:
            return Instance(instance=getattr(imported, "Main")(name=app_name, device=device_name), state=OK)
        else:
            logger.error('Cannot create app instance. app: {0}, device: {1}'.format(app_name, device_name))

    def __call__(self):
        return self.instance

    def shutdown(self):
        """Shuts down the Instance object.
        """
        self.instance.shutdown()
        self.state = 0

    def __repr__(self):
        output = {'instance': str(self.instance),
                  'state': str(self.state)}
        return str(output)
