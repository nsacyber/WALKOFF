import logging

from walkoff.executiondb.device import get_app as get_db_app
from apps.messaging import *
from walkoff.appgateway.decorators import *

_logger = logging.getLogger(__name__)


class App(object):
    """Base class for apps

    Attributes:
        app (apps.devicedb.App): The ORM of the App with the name passed into the constructor
        device (apps.devicedb.Device): The ORM of the device with the ID passed into teh constructor
        device_fields (dict): A dict of the plaintext fields of the device
        device_type (str): The type of device associated with self.device

    Args:
        app (str): The name of the app
        device (int): The ID of the device
    """

    _is_walkoff_app = True

    def __init__(self, app, device):
        self.app = get_db_app(app)
        self.device = self.app.get_device(device) if (self.app is not None and device) else None
        if self.device is not None:
            self.device_fields = self.device.get_plaintext_fields()
            self.device_type = self.device.type
        else:
            self.device_fields = {}
            self.device_type = None
        self.device_id = device

    def get_all_devices(self):
        """Gets all the devices associated with this app

        Returns:
            list: A list of apps.appdevice.Device objects associated with this app
        """
        return list(self.app.devices) if self.app is not None else []

    def shutdown(self):
        """When implemented, this method performs shutdown procedures for the app
        """
        pass
