import inspect
import logging
import os.path
import pkgutil
import sys
from importlib import import_module

from six import string_types

from walkoff.helpers import UnknownApp, UnknownAppAction, UnknownCondition, UnknownTransform
from .walkofftag import WalkoffTag

_logger = logging.getLogger(__name__)


class AppCache(object):
    """Object which caches app actions, conditions, and transforms

    Attributes:
        _cache (dict): The cache of the app and functions
    """
    # TODO: Use an enum for this? Something better than this anyways
    exception_lookup = {'actions': UnknownAppAction,
                        'conditions': UnknownCondition,
                        'transforms': UnknownTransform}

    def __init__(self):
        self._cache = {}

    def cache_apps(self, path):
        """Cache apps from a given path

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
                self._import_and_cache_submodules('{0}.{1}'.format(app_path, app), app, app_path)

    def clear(self):
        """Clears the cache
        """
        self._cache = {}

    def get_app_names(self):
        """Gets a list of all the app names

        Returns:
            list[str]: A list of all the names of apps stored in the cache
        """
        return list(self._cache.keys())

    def get_app(self, app_name):
        """Gets the app class for a given app.

        Args:
            app_name (str): Name of the app to get

        Returns:
            cls: The app's class

        Raises:
            UnknownApp: If the app is not found in the cache or the app has only global actions
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
        """Gets all the names of the actions for a given app

        Args:
            app_name (str): Name of the app

        Returns:
            list[str]: The actions associated with the app

        Raises:
            UnknownApp: If the app is not found in the cache
        """
        return self._get_function_type_names(app_name, 'actions')

    def get_app_action(self, app_name, action_name):
        """Gets the action function for a given app and action name

        Args:
            app_name (str): Name of the app
            action_name(str): Name of the action

        Returns:
            func: The action

        Raises:
            UnknownApp: If the app is not found in the cache
            UnknownAppAction: If the app does not have the specified action
        """
        return self._get_function_type(app_name, action_name, 'actions')

    def is_app_action_bound(self, app_name, action_name):
        """Determines if the action is bound (meaning it's inside a class) or not

        Args:
            app_name (str): Name of the app
            action_name(str): Name of the action

        Returns:
            bool: Is the action bound?

        Raises:
            UnknownApp: If the app is not found in the cache
            UnknownAppAction: If the app does not have the specified action
        """
        try:
            app_cache = self._cache[app_name]
            if 'actions' not in app_cache:
                _logger.warning('App {} has no actions'.format(app_name))
                raise UnknownAppAction(app_name, action_name)
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)
        try:
            return app_cache['actions'][action_name]['bound']
        except KeyError:
            _logger.error('App {0} has no action {1}'.format(app_name, action_name))
            raise UnknownAppAction(app_name, action_name)

    def get_app_condition_names(self, app_name):
        """Gets all the names of the conditions for a given app

        Args:
            app_name (str): Name of the app

        Returns:
            list[str]: The conditions associated with the app

        Raises:
            UnknownApp: If the app is not found in the cache
        """
        return self._get_function_type_names(app_name, 'conditions')

    def get_app_condition(self, app_name, condition_name):
        """Gets the condition function for a given app and action name

        Args:
            app_name (str): Name of the app
            condition_name(str): Name of the action

        Returns:
            func: The action

        Raises:
            UnknownApp: If the app is not found in the cache
            UnknownCondition: If the app does not have the specified condition
        """
        return self._get_function_type(app_name, condition_name, 'conditions')

    def get_app_transform_names(self, app_name):
        """Gets all the names of the transforms for a given app

        Args:
            app_name (str): Name of the app

        Returns:
            list[str]: The transforms associated with the app

        Raises:
            UnknownApp: If the app is not found in the cache
        """
        return self._get_function_type_names(app_name, 'transforms')

    def get_app_transform(self, app_name, transform_name):
        """Gets the transform function for a given app and action name

        Args:
            app_name (str): Name of the app
            transform_name(str): Name of the action

        Returns:
            func: The transform

        Raises:
            UnknownApp: If the app is not found in the cache
            UnknownCondition: If the app does not have the specified condition
        """
        return self._get_function_type(app_name, transform_name, 'transforms')

    def _get_function_type_names(self, app_name, function_type):
        """Gets all the names for a given function type ('actions', 'conditions', 'transforms') for an app

        Args:
            app_name (str): The name of the app
            function_type (str): 'actions', 'conditions' or 'transforms'

        Returns:
            list[str]: List of all the names of the functions of the given type

        Raises:
            UnknownApp: If the app is not found in the cache
        """
        try:
            app_cache = self._cache[app_name]
            if function_type not in app_cache:
                return []
            return list(app_cache[function_type].keys())
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)

    def _get_function_type(self, app_name, function_name, function_type):
        """Gets the function of the for a given app and action name

        Args:
            app_name (str): Name of the app
            function_name(str): Name of the action
            function_type (str): Type of function, 'actions', 'conditions', or 'transforms'

        Returns:
            func: The function

        Raises:
            UnknownApp: If the app is not found in the cache
            UnknownAppAction: if the function_type is 'actions' and the given action name isn't found
            UnknownCondition: if the function_type is 'conditions' and the given condition name isn't found
            UnknownTransform: if the function_type is 'transforms' and the given transform name isn't found
        """
        try:
            app_cache = self._cache[app_name]
            if function_type not in app_cache:
                _logger.warning('App {0} has no {1}.'.format(app_name, function_type))
                raise self.exception_lookup[function_type](app_name, function_name)
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)
        try:
            return app_cache[function_type][function_name]['run']
        except KeyError:
            _logger.error('App {0} has no {1} {2}'.format(app_name, function_type, function_name))
            raise self.exception_lookup[function_type](app_name, function_name)

    @staticmethod
    def _path_to_module(path):
        """Converts a path to a module. Can only handle relative paths without '..' in them.

        Args:
            path (str): Path to convert

        Returns:
            str: Module form of the path
        """
        path = path.replace(os.path.sep, '.')
        path = path.rstrip('.')
        return path.lstrip('.')

    def _import_and_cache_submodules(self, package, app_name, app_path, recursive=True):
        """Imports and caches the submodules from a given package.

        Args:
            package (str|module): The name of the package or the package itself from which to import the submodules.
            recursive (bool, optional): A boolean to determine whether or not to recursively load the submodules.
                Defaults to True.
        """
        successful_import = True
        if isinstance(package, string_types):
            try:
                package = import_module(package)
            except ImportError:
                _logger.exception('Cannot import {}. Skipping.'.format(package))
                successful_import = False
        if successful_import and package != sys.modules[__name__] and hasattr(package, '__path__'):
            for loader, name, is_package in pkgutil.walk_packages(package.__path__):
                if name != 'setup' and not name.startswith('tests'):
                    full_name = '{0}.{1}'.format(package.__name__, name)
                    try:
                        module = import_module(full_name)
                    except ImportError:
                        _logger.exception('Cannot import {}. Skipping.'.format(full_name))
                    else:
                        self._cache_module(module, app_name, app_path)
                        if recursive and is_package:
                            self._import_and_cache_submodules(full_name, app_name, app_path, recursive=True)

    def _cache_module(self, module, app_name, app_path):
        """Caches a module

        Args:
            module (module): The module to cache
            app_name (str): The name of the app associated with the module
        """
        base_path = '.'.join([app_path, app_name])
        for field, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and getattr(obj, '_is_walkoff_app', False)
                    and AppCache._get_qualified_class_name(obj) != 'apps.App'):
                self._cache_app(obj, app_name, base_path)
            elif inspect.isfunction(obj):
                for tag in WalkoffTag.get_tags(obj):
                    self._cache_action(obj, app_name, base_path, tag.name)

    def _cache_app(self, app_class, app_name, app_path):
        """Caches an app

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
        app_actions = inspect.getmembers(
            app_class, (lambda field:
                        (inspect.ismethod(field) or inspect.isfunction(field)) and WalkoffTag.action.is_tagged(field)))
        if 'actions' not in self._cache[app_name]:
            self._cache[app_name]['actions'] = {}
        if app_actions:
            new_actions = {}
            for _, action_method in app_actions:
                qualified_name = AppCache._get_qualified_function_name(action_method, cls=app_class)
                qualified_name = AppCache._strip_base_module_from_qualified_name(qualified_name, app_path)
                new_actions[qualified_name] = {'run': action_method, 'bound': True}
            self._cache[app_name]['actions'].update(new_actions)

    def _cache_action(self, action_method, app_name, app_path, tag, cls=None):
        """Caches an action

        Args:
            action_method (func): The action to cache
            app_name (str): The name of the app associated with the action
        """
        plural_tag = tag + 's'
        if app_name not in self._cache:
            self._cache[app_name] = {}
        if plural_tag not in self._cache[app_name]:
            self._cache[app_name][plural_tag] = {}
        qualified_action_name = AppCache._get_qualified_function_name(action_method, cls=cls)
        qualified_action_name = AppCache._strip_base_module_from_qualified_name(qualified_action_name, app_path)
        if qualified_action_name in self._cache[app_name][plural_tag]:
            _logger.warning(
                'App {0} already has {1}{2} {3} defined as {4}. Overwriting it with {5}'.format(
                    app_name,
                    ('unbound' if tag == 'action' else ''),
                    tag,
                    qualified_action_name,
                    AppCache._get_qualified_function_name(
                        self._cache[app_name][plural_tag][qualified_action_name]['run']),
                    qualified_action_name))
        self._cache[app_name][plural_tag][qualified_action_name] = {'run': action_method}
        if tag == 'action':
            self._cache[app_name][plural_tag][qualified_action_name]['bound'] = False

    def _clear_existing_bound_functions(self, app_name):
        """Clears existing bound functions from an app

        Args:
            app_name (str): The name of the app to clear
        """
        if 'actions' in self._cache[app_name]:
            self._cache[app_name]['actions'] = {
                action_name: action for action_name, action in self._cache[app_name]['actions'].items()
                if not action['bound']}

    @staticmethod
    def _get_qualified_class_name(obj):
        """Gets the qualified name of a class

        Args:
            obj (cls): The class to get the name

        Returns:
            str: The qualified name of the class
        """
        return '{0}.{1}'.format(obj.__module__, obj.__name__)

    @staticmethod
    def _get_qualified_function_name(method, cls=None):
        """Gets the qualified name of a function or method

        Args:
            method (func): The function or method to get the name
            cls (cls, optional): The class containing this function or method is any

        Returns:
            str: The qualified name of the function or method
        """
        if cls:
            return '{0}.{1}.{2}'.format(method.__module__, cls.__name__, method.__name__)
        else:
            return '{0}.{1}'.format(method.__module__, method.__name__)

    @staticmethod
    def _strip_base_module_from_qualified_name(qualified_name, base_module):
        """Strips a base module from a qualified name

        Args:
            qualified_name (str): The qualified name to strip
            base_module (str): The base module path to strip from the qualified name

        Returns:
            str: The stripped qualified name
        """
        base_module += '.'
        return qualified_name[len(base_module):] if qualified_name.startswith(base_module) else qualified_name
