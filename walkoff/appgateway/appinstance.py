import logging

from walkoff.appgateway import get_app

logger = logging.getLogger(__name__)


class AppInstance(object):
    def __init__(self, instance=None):
        """Initializes a new Instance of an App.
        
        Args:
            instance (Class): This is an instance of an App's module.
        """
        self.instance = instance

    @staticmethod
    def create(app_name, device_name, context):
        """Creates a new Instance object from an app name and a device name.
        
        Args:
            app_name (str): The name of the app from which to import the main module.
            device_name (str): A device pertaining to the App.
            context (dict): A dictionary of values representing the context in which the device is executing
            
        Returns:
            (AppInstance): A new Instance object.
        """
        try:
            app_class = get_app(app_name)
            app = app_class(app_name, device_name, context)
            return AppInstance(instance=app)
        except Exception:
            if device_name:
                logger.exception('Cannot create app instance. app: {0}, device: {1}.'.format(app_name, device_name))
            return AppInstance(instance=None)

    def __call__(self):
        return self.instance

    def shutdown(self):
        """Shuts down the Instance object."""
        self.instance.shutdown()
        self.instance._clear_cache()

    def __repr__(self):
        return str({'instance': str(self.instance)})
