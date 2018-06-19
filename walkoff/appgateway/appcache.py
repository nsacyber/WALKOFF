import inspect
import logging
import pkgutil
import sys
from collections import namedtuple
from importlib import import_module

import os.path
from six import string_types

from walkoff.appgateway.apiutil import UnknownApp, UnknownAppAction, UnknownCondition, UnknownTransform
from .walkofftag import WalkoffTag

_logger = logging.getLogger(__name__)

FunctionEntry = namedtuple('FunctionEntry', ['run', 'is_bound', 'tags'])


class AppCacheEntry(object):
    """An entry into the AppCache.

    Attributes:
        app_name (str): The name of the cached app
        main (cls): The main class inside the app which should be run with bounded functions. Defaults to None
        functions (dict{str: FunctionEntry}): A lookup dictionary of fully qualified path to FunctionEntry

    Args:
        app_name (str): The name of the app
    """
    __slots__ = ['app_name', 'main', 'functions']

    def __init__(self, app_name):
        self.app_name = app_name
        self.main = None
        self.functions = {}

    def cache_app_class(self, app_class, app_path):
        """Caches the app class

        Args:
            app_class (instance): Instance of the main method
            app_path (str): Path to the app module
        """
        if self.main is not None:
            _logger.warning(
                'App {0} already has class defined as {1}. Overwriting it with {2}'.format(
                    self.app_name,
                    _get_qualified_class_name(self.main),
                    _get_qualified_class_name(app_class)))
            self.clear_bound_functions()
        self.main = app_class
        app_methods = inspect.getmembers(
            app_class, (lambda field:
                        (inspect.ismethod(field) or inspect.isfunction(field)) and WalkoffTag.get_tags(field)))
        self.__cache_methods(app_methods, app_class, app_path)

    def __cache_methods(self, app_methods, app_class, app_path):
        for _, action_method in app_methods:
            tags = WalkoffTag.get_tags(action_method)
            qualified_name = _get_qualified_function_name(action_method, cls=app_class)
            qualified_name = _strip_base_module_from_qualified_name(qualified_name, app_path)
            self.functions[qualified_name] = FunctionEntry(run=action_method, is_bound=True, tags=tags)

    def cache_functions(self, functions, app_path):
        """Caches a group of functions

        Args:
            functions (list(tuple(func, set(WalkoffTag)))): The functions to cache
            app_path (str): Path to the app module
        """
        for function_, tags in functions:
            qualified_action_name = _get_qualified_function_name(function_)
            qualified_action_name = _strip_base_module_from_qualified_name(qualified_action_name, app_path)
            if qualified_action_name in self.functions:
                _logger.warning(
                    'App {0} already has {1} defined as {2}. Overwriting it with {3}'.format(
                        self.app_name,
                        qualified_action_name,
                        _get_qualified_function_name(self.functions[qualified_action_name].run),
                        qualified_action_name))
            self.functions[qualified_action_name] = FunctionEntry(run=function_, is_bound=False, tags=tags)

    def clear_bound_functions(self):
        """Clears any bounded functions from the object"""
        self.functions = {action_name: action for action_name, action in self.functions.items() if not action.is_bound}

    def is_bound(self, func_name):
        """Checks if a function is bound

        Args:
            func_name (str): The name of the function

        Returns:
            (bool): True if the function is bound, False otherwise

        Raises:
            UnknownAppAction: If the function name is not an existing function in the app
        """
        try:
            return self.functions[func_name].is_bound
        except KeyError:
            raise UnknownAppAction(self.app_name, func_name)

    def get_tagged_functions(self, tag):
        """Gets all tagged functions

        Args:
            tag (str): The tag to search by

        Returns:
            list[str]: A list of function names with the provided tag
        """
        return [function_name for function_name, entry in self.functions.items() if tag in entry.tags]

    def get_run(self, func_name, function_type):
        """Gets the function executable

        Args:
            func_name (str): The name of the function
            function_type (str): The type of the function

        Returns:
            (func): The function executable

        Raises:
            Exception: If the function type is not in the function entry tags
        """
        func_entry = self.functions[func_name]
        if function_type in func_entry.tags:
            return func_entry.run


class AppCache(object):
    """Object which caches app actions, conditions, and transforms

    Attributes:
        _cache (dict): The cache of the app and functions
    """
    # TODO: Use an enum for this? Something better than this anyways
    exception_lookup = {WalkoffTag.action: UnknownAppAction,
                        WalkoffTag.condition: UnknownCondition,
                        WalkoffTag.transform: UnknownTransform}

    def __init__(self):
        """Initializes a new AppCache object"""
        self._cache = {}

    def cache_apps(self, path, relative=True):
        """Cache apps from a given path

        Args:
            path (str): Path to apps module
            relative (bool): Whether the path should be relative or not
        """
        if not os.path.exists(path):
            raise RuntimeError("{} does not exist. Run `walkoff-run` inside a WALKOFF installation directory, "
                               "or specify a WALKOFF directory or config file with `walkoff-run -c`".format(path))
        sys.path.insert(0, os.path.abspath((os.path.dirname(path))))
        # dirs = next(os.walk(path))[1]
        # print("Path: " + path)
        # for module in dirs:
        #     print("Module: " + module)
        #     import_module(module)

        app_path = AppCache._path_to_module(path, relative=relative)
        # try:
        #     module = import_module(app_path)
        # except ImportError:
        #     _logger.exception('Cannot import base package for apps! No apps will be registered')
        # else:
        apps = next(os.walk(path))[1]
        for app in apps:
            self._import_and_cache_submodules('{0}.{1}'.format(app_path, app), app, app_path)

    def clear(self):
        """Clears the cache"""
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
            if app_cache.main is not None:
                return app_cache.main
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
        return self._get_function_type_names(app_name, WalkoffTag.action)

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
        return self._get_function_type(app_name, action_name, WalkoffTag.action)

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
            if not app_cache.functions:
                _logger.warning('App {} has no actions'.format(app_name))
                raise UnknownAppAction(app_name, action_name)
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)
        else:
            return app_cache.is_bound(action_name)

    def get_app_condition_names(self, app_name):
        """Gets all the names of the conditions for a given app

        Args:
            app_name (str): Name of the app

        Returns:
            list[str]: The conditions associated with the app

        Raises:
            UnknownApp: If the app is not found in the cache
        """
        return self._get_function_type_names(app_name, WalkoffTag.condition)

    def get_app_condition(self, app_name, condition_name):
        """Gets the condition function for a given app and action name

        Args:
            app_name (str): Name of the app
            condition_name(str): Name of the action

        Returns:
            (func): The action

        Raises:
            UnknownApp: If the app is not found in the cache
            UnknownCondition: If the app does not have the specified condition
        """
        return self._get_function_type(app_name, condition_name, WalkoffTag.condition)

    def get_app_transform_names(self, app_name):
        """Gets all the names of the transforms for a given app

        Args:
            app_name (str): Name of the app

        Returns:
            list[str]: The transforms associated with the app

        Raises:
            UnknownApp: If the app is not found in the cache
        """
        return self._get_function_type_names(app_name, WalkoffTag.transform)

    def get_app_transform(self, app_name, transform_name):
        """Gets the transform function for a given app and action name

        Args:
            app_name (str): Name of the app
            transform_name(str): Name of the action

        Returns:
            (func): The transform

        Raises:
            UnknownApp: If the app is not found in the cache
            UnknownCondition: If the app does not have the specified condition
        """
        return self._get_function_type(app_name, transform_name, WalkoffTag.transform)

    def _get_function_type_names(self, app_name, function_type):
        """Gets all the names for a given function type ('action', 'condition', 'transform') for an app

        Args:
            app_name (str): The name of the app
            function_type (WalkoffTag): tag to search for

        Returns:
            list[str]: List of all the names of the functions of the given type

        Raises:
            UnknownApp: If the app is not found in the cache
        """
        try:
            return self._cache[app_name].get_tagged_functions(function_type)
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)

    def _get_function_type(self, app_name, function_name, function_type):
        """Gets the function of the for a given app and action name

        Args:
            app_name (str): Name of the app
            function_name (str): Name of the action
            function_type (WalkoffTag): Type of function, 'actions', 'conditions', or 'transforms'

        Returns:
            (func): The function

        Raises:
            UnknownApp: If the app is not found in the cache
            UnknownAppAction: if the function_type is 'actions' and the given action name isn't found
            UnknownCondition: if the function_type is 'conditions' and the given condition name isn't found
            UnknownTransform: if the function_type is 'transforms' and the given transform name isn't found
        """
        try:
            app_cache = self._cache[app_name]
            if not app_cache.functions:
                _logger.warning('App {0} has no actions.'.format(app_name))
                raise self.exception_lookup[function_type](app_name, function_name)
        except KeyError:
            _logger.error('Cannot locate app {} in cache!'.format(app_name))
            raise UnknownApp(app_name)
        try:
            return app_cache.get_run(function_name, function_type)
        except KeyError:
            _logger.error('App {0} has no {1} {2}'.format(app_name, function_type.name, function_name))
            raise self.exception_lookup[function_type](app_name, function_name)

    @staticmethod
    def _path_to_module(path, relative=True):
        """Converts a path to a module. Handles relative paths without '..' in them, or just returns module name.

        Args:
            path (str): Path to convert

        Returns:
            (str): Module form of the path
        """
        if relative:
            path = path.replace(os.path.sep, '.')
            path = path.rstrip('.')
            return path.lstrip('.')
        else:
            directory, module_name = os.path.split(path)
            return module_name

    def _import_and_cache_submodules(self, package, app_name, app_path, recursive=True):
        """Imports and caches the submodules from a given package.

        Args:
            package (str|module): The name of the package or the package itself from which to import the submodules.
            app_name (str): The name of the app
            app_path (str): The path for the app
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
            app_path (str): The path of the app
        """
        base_path = '.'.join([app_path, app_name])
        global_actions = []
        for field, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and getattr(obj, '_is_walkoff_app', False)
                    and _get_qualified_class_name(obj) != 'appbase.App'):
                self._cache_app(obj, app_name, base_path)
            elif inspect.isfunction(obj):
                tags = WalkoffTag.get_tags(obj)
                if tags:
                    global_actions.append((obj, tags))
        if global_actions:
            if app_name not in self._cache:
                self._cache[app_name] = AppCacheEntry(app_name)
            self._cache[app_name].cache_functions(global_actions, base_path)

    def _cache_app(self, app_class, app_name, app_path):
        """Caches an app

        Args:
            app_class (cls): The app class to cache
            app_name (str): The name of the app associated with the class
            app_path (str): The path of the app
        """
        if app_name not in self._cache:
            self._cache[app_name] = AppCacheEntry(app_name)
        self._cache[app_name].cache_app_class(app_class, app_path)


def _get_qualified_class_name(obj):
    """Gets the qualified name of a class

    Args:
        obj (cls): The class to get the name

    Returns:
        (str): The qualified name of the class
    """
    return '{0}.{1}'.format(obj.__module__, obj.__name__)


def _get_qualified_function_name(method, cls=None):
    """Gets the qualified name of a function or method

    Args:
        method (func): The function or method to get the name
        cls (cls, optional): The class containing this function or method is any

    Returns:
        (str): The qualified name of the function or method
    """
    if cls:
        return '{0}.{1}.{2}'.format(method.__module__, cls.__name__, method.__name__)
    else:
        return '{0}.{1}'.format(method.__module__, method.__name__)


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
