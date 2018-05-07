import logging

from walkoff.appgateway import get_app
from walkoff.helpers import format_exception_message

logger = logging.getLogger(__name__)


class AppInstance(object):
    def __init__(self, instance=None):
        """Initializes a new Instance of an App.
        
        Args:
            instance (Class): This is an instance of an App's module.
        """
        self.instance = instance

    @staticmethod
    def create(app_name, device_name):
        """Creates a new Instance object from an app name and a device name.
        
        Args:
            app_name (str): The name of the app from which to import the main module.
            device_name (str): A device pertaining to the App.
            
        Returns:
            (AppInstance): A new Instance object.
        """
        try:
            return AppInstance(instance=get_app(app_name)(name=app_name, device=device_name))
        except Exception as e:
            if device_name:
                logger.exception('Cannot create app instance. app: {0}, device: {1}.'.format(app_name, device_name))
            return AppInstance(instance=None)

    def __call__(self):
        return self.instance

    def shutdown(self):
        """Shuts down the Instance object."""
        self.instance.shutdown()

    def __repr__(self):
        return str({'instance': str(self.instance)})
