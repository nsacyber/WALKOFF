from six import add_metaclass
import logging
import importlib
from core.decorators import *  # Change namespace of action
from blinker import NamedSignal

from core.helpers import UnknownApp, UnknownAppAction

_logger = logging.getLogger(__name__)


class AppRegistry(type):
    """
    Metaclass which registers metadata about all the apps
    Assumes apps are in module with <dir>.<app_name> structure
    """
    def __init__(cls, name, bases, nmspc):
        super(AppRegistry, cls).__init__(name, bases, nmspc)
        if not hasattr(cls, 'registry'):
            cls.registry = dict()
        app_name = cls._get_app_name()
        if app_name is not None:
            cls.registry[app_name] = {'main': cls,
                                      'display': cls.__get_display_function(),
                                      'actions': cls.__get_actions(nmspc)}

    def _get_app_name(cls):
        try:
            return cls.__module__.split('.')[1]
        except IndexError:
            return None

    def __get_display_function(cls):
        try:
            module_name = cls.__module__.rsplit('.', 1)[0]
            display_module = importlib.import_module('{0}.display'.format(module_name))
        except ImportError:
            # _logger.warning('App {0} has no module "display"'.format(cls._get_app_name()))
            return None
        else:
            try:
                load_function = getattr(display_module, 'load')
            except AttributeError:
                _logger.warning('App {0}.display has no property called "load"'.format(cls._get_app_name()))
                return None
            else:
                if callable(load_function):
                    return load_function
                else:
                    _logger.warning('App {0}.display.load is not callable'.format(cls._get_app_name()))
                    return None

    def __get_actions(cls, nmspc):
        actions = {}
        for property_name, property_value in nmspc.items():
            if callable(property_value) and getattr(property_value, 'action', False):
                actions[property_name] = getattr(cls, property_name)
        return actions


@add_metaclass(AppRegistry)
class App(object):
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


def get_app(app_name):
    try:
        return App.registry[app_name]['main']
    except KeyError:
        raise UnknownApp(app_name)


def get_all_actions_for_app(app_name):
    try:
        return App.registry[app_name]['actions']
    except KeyError:
        raise UnknownApp(app_name)


def get_app_action(app_name, action_name):
    try:
        app = App.registry[app_name]
    except KeyError:
        raise UnknownApp(app_name)
    else:
        try:
            return app['actions'][action_name]
        except:
            raise UnknownAppAction(app_name, action_name)


def get_app_display(app_name):
    try:
        return App.registry[app_name]['display']
    except KeyError:
        raise UnknownApp(app_name)


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
