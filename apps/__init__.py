from six import add_metaclass, string_types
import logging
import importlib
from core.decorators import *  # Change namespace of action
from blinker import NamedSignal
import pkgutil
from importlib import import_module
import inspect
import os.path
from core.helpers import format_exception_message, UnknownApp, UnknownAppAction

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


class AppCache(object):

    def __init__(self):
        self._cache = {}

    def cache_apps(self, path):
        app_path = AppCache._path_to_module(path)
        try:
            module = import_module(app_path)
        except ImportError:
            _logger.error('Cannot import base package for apps! No apps will be registered')
        else:
            apps = [info[1] for info in pkgutil.walk_packages(module.__path__)]
            for app in apps:
                 self._import_and_cache_submodules('{0}.{1}'.format(app_path, app), app)

    def clear(self):
        self._cache = {}

    def get_app_names(self):
        return list(self._cache.keys())

    def get_app(self, app_name):
        try:
            app_cache = self._cache[app_name]
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)
        else:
            if 'main' in app_cache:
                return app_cache['main']
            else:
                _logger.warning('App {} has no class.'.format(app_name))
                raise UnknownApp(app_name)

    def get_app_action_names(self, app_name):
        try:
            app_cache = self._cache[app_name]
            if 'actions' not in app_cache:
                return []
            return list(app_cache['actions'].keys())
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)

    def get_app_action(self, app_name, action_name):
        try:
            app_cache = self._cache[app_name]
            if 'actions' not in app_cache:
                _logger.warning('App {} has no actions. Returning None'.format(app_name))
                raise UnknownAppAction(app_name, action_name)
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)
        try:
            return app_cache['actions'][action_name]['run']
        except KeyError:
            _logger.error('App {0} has no action {1}'.format(app_name, action_name))
            raise UnknownAppAction(app_name, action_name)

    def is_app_action_bound(self, app_name, action_name):
        try:
            app_cache = self._cache[app_name]
            if 'actions' not in app_cache:
                _logger.warning('App {} has no actions. Returning None'.format(app_name))
                raise UnknownAppAction(app_name, action_name)
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)
        try:
            return app_cache['actions'][action_name]['bound']
        except KeyError:
            _logger.error('App {0} has no action {1}'.format(app_name, action_name))
            raise UnknownAppAction(app_name, action_name)

    @staticmethod
    def list_apps(path):
        try:
            return [f for f in os.listdir(path)
                    if (os.path.isdir(os.path.join(path, f))
                        and not f.startswith('__'))]
        except (IOError, OSError) as e:
            _logger.error(
                'Cannot get valid directories inside {0}. Error: {1}'.format(path, format_exception_message(e)))
            return []

    @staticmethod
    def _path_to_module(path):
        path = path.replace(os.path.sep, '.')
        path = path.rstrip('.')
        return path.lstrip('.')

    def _import_and_cache_submodules(self, package, app_name, recursive=True):
        """Imports the submodules from a given package.

            Args:
                package (str|module): The name of the package from which to import the submodules.
                recursive (bool, optional): A boolean to determine whether or not to recursively load the submodules.
                    Defaults to False.

            Returns:
                A dictionary containing the imported module objects.
            """
        if isinstance(package, string_types):
            package = import_module(package)
        for loader, name, is_package in pkgutil.walk_packages(package.__path__):
            full_name = '{0}.{1}'.format(package.__name__, name)
            try:
                module = import_module(full_name)
            except ImportError as e:
                _logger.error('Cannot import {0}. Reason: {1}. Skipping.'.format(full_name, format_exception_message(e)))
            else:
                self._cache_module(module, app_name)
                if recursive and is_package:
                    self._import_and_cache_submodules(full_name, app_name, recursive=True)

    def _cache_module(self, module, app_name):
        for field, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and App in obj.__bases__:
                self._cache_app(obj, app_name)
            elif inspect.isfunction(obj) and hasattr(obj, 'action'):
                self._cache_action(field, obj, app_name)

    def _cache_app(self, app_class, app_name):
        if app_name not in self._cache:
            self._cache[app_name] = {}
        if 'main' in self._cache[app_name] and self._cache[app_name]['main']:
            _logger.warning(
                'App {0} already has class defined as {1}. Overwriting it with {2}'.format(
                    app_name,
                    AppCache._get_qualified_class_name(self._cache[app_name]['main']),
                    AppCache._get_qualified_class_name(app_class)))
            self._clear_existing_bound_functions(app_name)
        self._cache[app_name]['main'] = app_class
        app_actions = inspect.getmembers(app_class, (lambda field: inspect.ismethod(field) and hasattr(field, 'action')))
        if 'actions' not in self._cache[app_name]:
            self._cache[app_name]['actions'] = {}
        if app_actions:
            self._cache[app_name]['actions'].update({action_name: {'run': action_method, 'bound': True}
                                                     for action_name, action_method in dict(app_actions).items()})

    def _cache_action(self, action_name, action_method, app_name):
        if app_name not in self._cache:
            self._cache[app_name] = {}
        if 'actions' not in self._cache[app_name]:
            self._cache[app_name]['actions'] = {}
        if action_name in self._cache[app_name]['actions']:
            _logger.warning(
                'App {0} already has unbound action {1} defined as {2}. Overwriting it with {3}'.format(
                    app_name,
                    action_name,
                    AppCache._get_qualified_function_name(self._cache[app_name]['actions'][action_name]['run']),
                    AppCache._get_qualified_function_name(action_method)))

        self._cache[app_name]['actions'][action_name] = {'run': action_method, 'bound': False}

    def _clear_existing_bound_functions(self, app_name):
        if 'actions' in self._cache[app_name]:
            for action_name, action_ in self._cache[app_name]['actions'].items():
                if action_['bound']:
                    self._cache[app_name]['actions'].pop(action_name)

    @staticmethod
    def _get_qualified_class_name(obj):
        return '{0}.{1}'.format(obj.__module__, obj.__name__)

    @staticmethod
    def _get_qualified_function_name(method):
        return '{0}.{1}'.format(method.__module__, method.__name__)


_cache = AppCache()


def get_app(app_name):
    return _cache.get_app(app_name)


def get_all_actions_for_app(app_name):
    return _cache.get_app_action_names(app_name)


def get_app_action(app_name, action_name):
    return _cache.get_app_action(app_name, action_name)


def cache_apps(path):
    _cache.cache_apps(path)


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
