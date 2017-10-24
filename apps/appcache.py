import inspect
import pkgutil
from importlib import import_module
import os.path
from six import string_types
import sys
import logging
from core.helpers import UnknownApp, UnknownAppAction, format_exception_message

_logger = logging.getLogger(__name__)


class AppCache(object):
    """
    Object which caches app actions
    """

    def __init__(self):
        self._cache = {}

    def cache_apps(self, path):
        """
        Cache apps from a given path

        Args:
            path (str): Path to apps module
        """
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
        """
        Clears the cache
        """
        self._cache = {}

    def get_app_names(self):
        """
        Gets a list of all the app names
        """
        return list(self._cache.keys())

    def get_app(self, app_name):
        """
        Gets the app class for a given app. If app has only global actions or is not found,
        raises an UnknownApp exception.

        Args:
            app_name (str): Name of the app to get

        Returns:
            (cls) The app's class
        """
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
        """
        Gets all the names of the actions for a given app

        Args:
            app_name (str): Name of the app

        Returns:
            (list[str]): The actions associated with the app
        """
        try:
            app_cache = self._cache[app_name]
            if 'actions' not in app_cache:
                return []
            return list(app_cache['actions'].keys())
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)

    def get_app_action(self, app_name, action_name):
        """
        Gets the action function for a given app and action name

        Args:
            app_name (str): Name of the app
            action_name(str): Name of the action

        Returns:
            (func) The action
        """
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
        """
        Determines if the action is bound (meaning it's inside a class) or not

        Args:
            app_name (str): Name of the app
            action_name(str): Name of the action

        Returns:
            (bool) Is the action bound?
        """
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
    def _path_to_module(path):
        """
        Converts a path to a module. Can only handle relative paths without '..' in them.

        Args:
            path (str): Path to convert

        Returns:
            (str) Module form of the path
        """
        path = path.replace(os.path.sep, '.')
        path = path.rstrip('.')
        return path.lstrip('.')

    def _import_and_cache_submodules(self, package, app_name, recursive=True):
        """Imports and caches the submodules from a given package.

            Args:
                package (str|module): The name of the package or the package itself from which to import the submodules.
                recursive (bool, optional): A boolean to determine whether or not to recursively load the submodules.
                    Defaults to True.
            """
        if isinstance(package, string_types):
            package = import_module(package)
        if package != sys.modules[__name__]:
            for loader, name, is_package in pkgutil.walk_packages(package.__path__):
                if name != 'setup':
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
        """
        Caches a module

        Args:
            module (module): The module to cache
            app_name (str): The name of the app associated with the module
        """
        for field, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and getattr(obj, '_is_walkoff_app', False)
                    and AppCache._get_qualified_class_name(obj) != 'apps.App'):
                self._cache_app(obj, app_name)
            elif inspect.isfunction(obj) and hasattr(obj, 'action'):
                self._cache_action(field, obj, app_name)

    def _cache_app(self, app_class, app_name):
        """
        Caches an app

        Args:
            app_class (cls): The app class to cache
            app_name (str): The name of the app associated with the class
        """
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
        app_actions = inspect.getmembers(app_class,
                                         (lambda field: (inspect.ismethod(field) or inspect.isfunction(field))
                                                        and hasattr(field, 'action')))
        if 'actions' not in self._cache[app_name]:
            self._cache[app_name]['actions'] = {}
        if app_actions:
            self._cache[app_name]['actions'].update({action_name: {'run': action_method, 'bound': True}
                                                     for action_name, action_method in dict(app_actions).items()})

    def _cache_action(self, action_name, action_method, app_name):
        """
        Caches an action

        Args:
            action_name (str): The name of the action
            action_method (func): The action to cache
            app_name (str): The name of the app associated with the action
        """
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
        """
        Clears existing bound functions from an app

        Args:
            app_name (str): The name of the app to clear
        """
        if 'actions' in self._cache[app_name]:
            self._cache[app_name]['actions'] = {
                action_name: action for action_name, action in self._cache[app_name]['actions'].items()
                if not action['bound']}

    @staticmethod
    def _get_qualified_class_name(obj):
        """
        Gets the qualified name of a class

        Args:
            obj (cls): The class to get the name

        Returns:
            (str) The qualified name of the class
        """
        return '{0}.{1}'.format(obj.__module__, obj.__name__)

    @staticmethod
    def _get_qualified_function_name(method):
        """
        Gets the qualified name of a function or method

        Args:
            method (func): The function or method to get the name

        Returns:
            (str) The qualified name of the function or method
        """
        return '{0}.{1}'.format(method.__module__, method.__name__)