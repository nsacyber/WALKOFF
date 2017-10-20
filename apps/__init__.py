import logging
from core.decorators import *
from apps.appcache import AppCache

_logger = logging.getLogger(__name__)


class App(object):

    _is_walkoff_app = True

    def __init__(self, app, device):
        self.app = app
        self.device = device

    def get_all_devices(self):
        """ Gets all the devices associated with this app """
        from server.appdevice import App as _App
        return _App.get_all_devices_for_app(self.app)

    def get_device(self):
        """ Gets the device associated with this app """
        from server.appdevice import App as _App
        return _App.get_device(self.app, self.device)

    def shutdown(self):
        """ When implemented, this method performs shutdown procedures for the app """
        pass


_cache = AppCache()


def get_app(app_name):
    return _cache.get_app(app_name)


def get_all_actions_for_app(app_name):
    return _cache.get_app_action_names(app_name)


def get_app_action(app_name, action_name):
    return _cache.get_app_action(app_name, action_name)


def cache_apps(path):
    _cache.cache_apps(path)


def clear_cache():
    _cache.clear()


def is_app_action_bound(app_name, action_name):
    return _cache.is_app_action_bound(app_name, action_name)


class AppWidgetBlueprint(object):
    def __init__(self, blueprint, rule=''):
        self.blueprint = blueprint
        self.rule = rule

AppBlueprint = AppWidgetBlueprint
WidgetBlueprint = AppWidgetBlueprint


class Event(object):
    """
    Encapsulated an asynchronous event.

    Attributes:
        name (str, optional): Name of the event. Defaults to ''
        receivers (set{func}): Set of functions waiting on the event
    """
    def __init__(self, name=''):
        """
        Constructor

        Args:
             name (str, optional): Name of the Event. Defaults to ''
        """
        self.name = name
        self.receivers = set()

    def connect(self, func):
        """
        Connects a function to the event as a callback

        Args:
            func (func): Function to register as a callback
        Returns:
            (func): The unmodified function
        """
        self.receivers.add(func)
        return func

    def disconnect(self, func):
        """
        Disconnects a function

        Args:
            func (func): The function to disconnect
        """
        try:
            self.receivers.remove(func)
        except KeyError:
            pass

    def trigger(self, data):
        """
        Triggers an event and calls all the functions with the data provided

        Args:
            data: Data to send to all the callbacks registered to this event

        """
        for func in self.receivers:
            func(data)
