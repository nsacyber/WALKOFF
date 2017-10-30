import importlib
import json
import logging
import os
import pkgutil
import sys

from six import string_types

import core.config.config
import core.config.paths

try:
    from importlib import reload as reload_module
except ImportError:
    from imp import reload as reload_module

__new_inspection = False
if sys.version_info.major >= 3 and sys.version_info.minor >= 3:
    from inspect import signature as getsignature

    __new_inspection = True
else:
    from inspect import getargspec as getsignature


logger = logging.getLogger(__name__)


def import_py_file(module_name, path_to_file):
    """Dynamically imports a python module.
    
    Args:
        module_name (str): The name of the module to be imported.
        path_to_file (str): The path to the module to be imported.
        
    Returns:
        The module object that was imported.
    """
    if sys.version_info[0] == 2:
        from imp import load_source
        import exceptions, warnings
        with warnings.catch_warnings(record=True) as w:
            imported = load_source(module_name, os.path.abspath(path_to_file))
            if w:
                mod_name = module_name.replace('.main','')
                if not (type(w[-1].category) == type(exceptions.RuntimeWarning) or
                        'Parent module \'apps.'+mod_name+'\' not found while handling absolute import' in w[-1].message):
                    print(w[-1].message)
    else:
        from importlib import machinery
        loader = machinery.SourceFileLoader(module_name, os.path.abspath(path_to_file))
        imported = loader.load_module(module_name)
    return imported


def import_lib(directory, module_name):
    """Dynamically imports a Python library.
    
    Args:
        directory (str): The directory in which the library is located.
        module_name (str): The name of the library to be imported.
        
    Returns:
        The module object that was imported.
    """
    imported_module = None
    module_name = '.'.join(['core', directory, module_name])
    try:
        imported_module = importlib.import_module(module_name)
    except ImportError:
        logger.error('Cannot import module {0}. Returning None'.format(module_name))
        pass
    finally:

        return imported_module


def construct_module_name_from_path(path):
    """Constructs the name of the module with the path name.
    
    Args:
        path (str): The path to the module.
        
    Returns:
         The name of the module with the path name.
    """
    path = path.lstrip('.{0}'.format(os.sep))
    path = path.replace('.', '')
    return '.'.join([x for x in path.split(os.sep) if x])


def import_app_main(app_name, path=None, reload=False):
    """Dynamically imports the main function of an App.
    
    Args:
        app_name (str): The name of the App from which to import the main function.
        path (str, optional): The path to the apps module. Defaults to core.config.paths.apps_path
        reload (bool, optional): Reload the module if already imported. Defaults to True
    Returns:
        The module object that was imported.
    """
    if path is None:
        path = core.config.paths.apps_path
    app_path = os.path.join(path, app_name, 'main.py')
    module_name = construct_module_name_from_path(app_path[:-3])
    try:
        module = sys.modules[module_name]
        if reload:
            reload_module(module)
        return module
    except KeyError:
        pass
    try:
        imported_module = import_py_file(module_name, app_path)
        sys.modules[module_name] = imported_module
        return imported_module
    except (ImportError, IOError, OSError, SyntaxError) as e:
        logger.error('Cannot load app main for app {0}. Error: {1}'.format(app_name, format_exception_message(e)))
        pass


def __list_valid_directories(path):
    try:
        return [f for f in os.listdir(path)
                if (os.path.isdir(os.path.join(path, f))
                    and not f.startswith('__'))]
    except (IOError, OSError) as e:
        logger.error('Cannot get valid directories inside {0}. Error: {1}'.format(path, format_exception_message(e)))
        return []


def list_apps(path=None):
    """Get a list of the apps.
    
    Args:
        path (str, optional): The path to the apps folder. Default is None.
        
    Returns:
        A list of the apps given the apps path or the apps_path in the configuration.
    """
    if path is None:
        path = core.config.paths.apps_path
    return __list_valid_directories(path)


def list_apps_with_interfaces(path=None):
    if path is None:
        path = core.config.paths.apps_path
    apps = list_apps(path)
    apps_with_interfaces = []
    for app in apps:
        app_path = os.path.join(path, app, 'interface', 'templates', 'index.html')
        if os.path.isfile(app_path):
            apps_with_interfaces.append(app)

    return apps_with_interfaces


def list_apps_with_device_types():
    return [app for app, api in core.config.config.app_apis.items() if 'devices' in api]


def list_widgets(app, app_path=None):
    """Get a list of the widgets for a given app. 
    
    Args:
        app (str): The app under which the widgets are located.
        app_path (str, optional): The path to the widgets folder. Default is None.
        
    Returns:
        A list of the widgets given the apps path or the apps_path in the configuration.
    """
    if app_path is None:
        app_path = core.config.paths.apps_path
    return __list_valid_directories(os.path.join(app_path, app, 'widgets'))


def list_class_functions(class_name):
    """Get the functions for a python Class.
    
    Args:
        class_name (str): The name of the python Class from which to get the functions.
        
    Returns:
        The list of functions for a given python Class.
    """
    return [field for field in dir(class_name) if (not field.startswith('_')
                                                   and callable(getattr(class_name, field)))]


def locate_playbooks_in_directory(path=None):
    """Get a list of workflows in a specified directory or the workflows_path directory as specified in the configuration.
    
    Args:
        path (str, optional): The directory path from which to locate the workflows. Defaults to None.
        
    Returns:
        A list of workflow names from the specified path, or the directory specified in the configuration.
    """
    path = path if path is not None else core.config.paths.workflows_path
    if os.path.exists(path):
        return [workflow for workflow in os.listdir(path) if (os.path.isfile(os.path.join(path, workflow))
                                                              and workflow.endswith('.playbook'))]
    else:
        logger.warning('Could not locate any workflows in directory {0}. Directory does not exist'.format(path))
        return []


def get_workflow_names_from_file(filename):
    """Get a list of workflow names in a given file.
    
    Args:
        filename (str): The filename from which to locate the workflows.
        
    Returns:
        A list of workflow names from the specified file, if the file exists.
    """
    if os.path.isfile(filename):
        with open(filename, 'r') as playbook_file:
            playbook = playbook_file.read()
            playbook = json.loads(playbook)
            return [workflow['name'] for workflow in playbook['workflows']]
    return []


def combine_dicts(x, y):
    """Combines two dictionaries into one.
    
    Args:
        x (dict): One dictionary to be merged.
        y (dict): The other dictionary to be merged with x.
        
    Returns:
        The merged dictionary.
    """
    z = x.copy()
    z.update(y)
    return z


def import_submodules(package, recursive=False):
    """Imports the submodules from a given package.

    Args:
        package (str): The name of the package from which to import the submodules.
        recursive (bool, optional): A boolean to determine whether or not to recursively load the submodules.
            Defaults to False.

    Returns:
        A dictionary containing the imported module objects.
    """
    successful_base_import = True
    if isinstance(package, str):
        try:
            package = importlib.import_module(package)
        except ImportError:
            successful_base_import = False
            logger.warning('Could not import {}. Skipping'.format(package), exc_info=True)
    if successful_base_import:
        results = {}
        for loader, name, is_package in pkgutil.walk_packages(package.__path__):
            full_name = '{0}.{1}'.format(package.__name__, name)
            try:
                results[full_name] = importlib.import_module(full_name)
            except ImportError:
                logger.warning('Could not import {}. Skipping.'.format(full_name), exc_info=True)
            if recursive and is_package:
                results.update(import_submodules(full_name))
        return results
    return {}


def format_db_path(db_type, path):
    """
    Formats the path to the database

    Args:
        db_type (str): Type of database being used
        path (str): Path to the database

    Returns:
        (str): The path of the database formatted for SqlAlchemy
    """
    return '{0}://{1}'.format(db_type, path) if db_type != 'sqlite' else '{0}:///{1}'.format(db_type, path)


def get_app_action_api(app, action):
    """
    Gets the api for a given app and action

    Args:
        app (str): Name of the app
        action (str): Name of the action

    Returns:
        (tuple(str, dict)) The name of the function to execute and its parameters
    """
    try:
        app_api = core.config.config.app_apis[app]
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            action_api = app_api['actions'][action]
            run = action_api['run']
            return run, action_api.get('parameters', [])
        except KeyError:
            raise UnknownAppAction(app, action)


def get_app_device_api(app, device_type):
    try:
        app_api = core.config.config.app_apis[app]
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            return app_api['devices'][device_type]
        except KeyError:
            raise UnknownDevice(app, device_type)


def __split_api_params(api):
    data_param_name = api['dataIn']
    args = []
    data_param = None
    for api_param in api['parameters']:
        if api_param['name'] == data_param_name:
            data_param = api_param
        else:
            args.append(api_param)
    if data_param is None:  # This should be validated by the schema, but just in case
        raise ValueError
    return args, data_param


def get_condition_api(condition):
    try:
        api = core.config.config.function_apis['conditions'][condition]
        return __split_api_params(api)
    except (KeyError, ValueError):
        raise UnknownCondition(condition)


def get_condition(condition):
    try:
        runnable = core.config.config.function_apis['conditions'][condition]['run']
        return core.config.config.conditions[runnable]
    except KeyError:
        raise UnknownCondition(condition)


def get_transform_api(transform):
    try:
        api = core.config.config.function_apis['transforms'][transform]
        return __split_api_params(api)
    except (KeyError, ValueError):
        raise UnknownTransform(transform)


def get_transform(transform):
    try:
        runnable = core.config.config.function_apis['transforms'][transform]['run']
        return core.config.config.transforms[runnable]
    except KeyError:
        raise UnknownTransform(transform)


class InvalidAppStructure(Exception):
    pass


class UnknownApp(Exception):
    def __init__(self, app):
        super(UnknownApp, self).__init__('Unknown app {0}'.format(app))
        self.app = app


class UnknownAppAction(Exception):
    def __init__(self, app, action_name):
        super(UnknownAppAction, self).__init__('Unknown action {0} for app {1}'.format(action_name, app))
        self.app = app
        self.action = action_name


class UnknownDevice(Exception):
    def __init__(self, app, device_type):
        super(UnknownDevice, self).__init__('Unknown device {0} for device {1} '.format(app, device_type))
        self.app = app
        self.device_type = device_type


class InvalidInput(Exception):
    def __init__(self, message):
        self.message = message
        super(InvalidInput, self).__init__(self.message)


class UnknownCondition(Exception):
    def __init__(self, condition):
        self.message = 'Unknown condition {0}'.format(condition)
        super(UnknownCondition, self).__init__(self.message)
        self.condition = condition


class UnknownTransform(Exception):
    def __init__(self, transform):
        self.message = 'Unknown transform {0}'.format(transform)
        super(UnknownTransform, self).__init__(self.message)
        self.transform = transform


def __get_tagged_functions(module, tag, prefix):
    tagged = {}
    start_index = len(prefix)+1
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if not attr_name.startswith('_') and callable(attr) and getattr(attr, tag, False):
            name = '{0}.{1}'.format(module.__name__, attr_name)[start_index:]
            tagged[name] = attr
    return tagged


def import_and_find_tags(package, tag, prefix=None, recursive=True):
    """Imports the submodules from a given package and finds functions tagged with given tag.

    Args:
        package (str): The name of the package from which to import the submodules.
        tag (str): The tag to look for
        recursive (bool, optional): A boolean to determine whether or not to recursively load the submodules.
            Defaults to False.

    Returns:
        A dictionary of the form {<function_name>: <function>}.
    """

    tagged = {}
    successful_base_import = True
    if isinstance(package, str):
        prefix = package if prefix is None else prefix
        try:
            package = importlib.import_module(package)
        except ImportError:
            successful_base_import = False
            logger.warning('Could not import {}. Skipping'.format(package), exc_info=True)
        tagged.update(__get_tagged_functions(package, tag, prefix))
    if successful_base_import:
        for loader, name, is_package in pkgutil.walk_packages(package.__path__):
            full_name = '{0}.{1}'.format(package.__name__, name)
            try:
                module = importlib.import_module(full_name)
            except ImportError:
                logger.warning('Could not import {}. Skipping'.format(package), exc_info=True)
            else:
                tagged.update(__get_tagged_functions(module, tag, prefix))
                if recursive and is_package:
                    tagged.update(import_and_find_tags(full_name, tag, prefix=prefix))
        return tagged


def import_all_conditions(package='core.conditions'):
    return import_and_find_tags(package, 'condition')


def import_all_transforms(package='core.transforms'):
    return import_and_find_tags(package, 'transform')


def __get_step_from_reference(reference, accumulator, message_prefix):
    input_step_name = reference[1:]
    if input_step_name in accumulator:
        return accumulator[input_step_name]
    else:
        message = ('{0}: Referenced step {1} '
                   'has not been executed'.format(message_prefix, input_step_name))
        raise InvalidInput(message)


# TODO: Rewrite this using generators. Python doesn't play nice with recursion
def dereference_step_routing(input_, accumulator, message_prefix):
    if isinstance(input_, dict):
        return {input_name: dereference_step_routing(input_value, accumulator, message_prefix)
                for input_name, input_value in input_.items()}
    elif isinstance(input_, list):
        return [dereference_step_routing(element, accumulator, message_prefix) for element in input_]
    else:
        if isinstance(input_, string_types) and input_.startswith('@'):
            return __get_step_from_reference(input_, accumulator, message_prefix)
        else:
            return input_


def get_function_arg_names(func):
    if __new_inspection:
        return list(getsignature(func).parameters.keys())
    else:
        return getsignature(func).args


class InvalidApi(Exception):
    pass


def format_exception_message(exception):
    exception_message = str(exception)
    class_name = exception.__class__.__name__
    return '{0}: {1}'.format(class_name, exception_message) if exception_message else class_name
