import importlib
import json
import logging
import os
import pkgutil
import sys

import walkoff.config.config
import walkoff.config.paths

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
                mod_name = module_name.replace('.main', '')
                if not (type(w[-1].category) == type(exceptions.RuntimeWarning) or
                                        'Parent module \'apps.' + mod_name + '\' not found while handling absolute import' in
                                w[-1].message):
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
        path = walkoff.config.paths.apps_path
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
        path = walkoff.config.paths.apps_path
    return __list_valid_directories(path)


def list_interfaces(path=None):
    if path is None:
        path = walkoff.config.paths.interfaces_path
    return __list_valid_directories(path)


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
    path = path if path is not None else walkoff.config.paths.workflows_path
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
        if hasattr(package, '__path__'):
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
        app_api = walkoff.config.config.app_apis[app]
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            action_api = app_api['actions'][action]
            run = action_api['run']
            return run, action_api.get('parameters', [])
        except KeyError:
            raise UnknownAppAction(app, action)


def get_app_action_default_return(app, action):
    """
    Gets the default return code for a given app and action

    Args:
        app (str): Name of the app
        action (str): Name of the action

    Returns:
        (str): The name of the default return code or Success if none defined
    """
    try:
        app_api = walkoff.config.config.app_apis[app]
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            action_api = app_api['actions'][action]
            if 'default_return' in action_api:
                return action_api['default_return']
            else:
                return 'Success'
        except KeyError:
            raise UnknownAppAction(app, action)


def get_app_action_return_is_failure(app, action, status):
    """
    Checks the api for whether a status code is a failure code for a given app and action

    Args:
        app (str): Name of the app
        action (str): Name of the action
        status (str): Name of the status

    Returns:
        (boolean): True if status is a failure code, false otherwise
    """
    try:
        app_api = walkoff.config.config.app_apis[app]
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            action_api = app_api['actions'][action]
            if 'failure' in action_api['returns'][status]:
                return True if action_api['returns'][status]['failure'] is True else False
            else:
                return False
        except KeyError:
            raise UnknownAppAction(app, action)


def get_app_device_api(app, device_type):
    try:
        app_api = walkoff.config.config.app_apis[app]
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            return app_api['devices'][device_type]
        except KeyError:
            raise UnknownDevice(app, device_type)


def split_api_params(api, data_param_name):
    args = []
    for api_param in api:
        if api_param['name'] != data_param_name:
            args.append(api_param)
    return args


def get_condition_api(app, condition):
    try:
        app_api = walkoff.config.config.app_apis[app]
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            condition_api = app_api['conditions'][condition]
            run = condition_api['run']
            return condition_api['data_in'], run, condition_api.get('parameters', [])
        except KeyError:
            raise UnknownCondition(app, condition)


def get_transform_api(app, transform):
    try:
        app_api = walkoff.config.config.app_apis[app]
    except KeyError:
        raise UnknownApp(app)
    else:
        try:
            transform_api = app_api['transforms'][transform]
            run = transform_api['run']
            return transform_api['data_in'], run, transform_api.get('parameters', [])
        except KeyError:
            raise UnknownTransform(app, transform)


class InvalidAppStructure(Exception):
    pass


class UnknownApp(Exception):
    def __init__(self, app):
        super(UnknownApp, self).__init__('Unknown app {0}'.format(app))
        self.app = app


class UnknownFunction(Exception):
    def __init__(self, app, function_name, function_type):
        self.message = 'Unknown {0} {1} for app {2}'.format(function_type, function_name, app)
        super(UnknownFunction, self).__init__(self.message)
        self.app = app
        self.function = function_name


class UnknownAppAction(UnknownFunction):
    def __init__(self, app, action_name):
        super(UnknownAppAction, self).__init__(app, action_name, 'action')


class UnknownDevice(Exception):
    def __init__(self, app, device_type):
        super(UnknownDevice, self).__init__('Unknown device {0} for device {1} '.format(app, device_type))
        self.app = app
        self.device_type = device_type


class InvalidArgument(Exception):
    def __init__(self, message):
        self.message = message
        super(InvalidArgument, self).__init__(self.message)


class UnknownCondition(UnknownFunction):
    def __init__(self, app, condition_name):
        super(UnknownCondition, self).__init__(app, condition_name, 'condition')


class UnknownTransform(UnknownFunction):
    def __init__(self, app, transform_name):
        super(UnknownTransform, self).__init__(app, transform_name, 'transform')


class InvalidExecutionElement(Exception):
    def __init__(self, id_, name, message):
        self.id = id_
        self.name = name
        super(InvalidExecutionElement, self).__init__(message)


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


def convert_action_argument(argument):
    for field in ('value', 'selection'):
        if field in argument:
            try:
                argument[field] = json.loads(argument[field])
            except ValueError:
                pass
    return argument


def create_sse_event(event_id=None, event=None, data=None):
    if data is None and event_id is None and event is None:
        return ''
    response = ''
    if event_id is not None:
        response += 'id: {}\n'.format(event_id)
    if event is not None:
        response += 'event: {}\n'.format(event)
    if data is not None:
        try:
            response += 'data: {}\n'.format(json.dumps(data))
        except ValueError:
            response += 'data: {}\n'.format(data)
    return response + '\n'
