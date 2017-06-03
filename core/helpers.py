import importlib
import sys
import os
from xml.etree import ElementTree
import pkgutil
import logging
import core.config.paths
from functools import wraps

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
        imported = load_source(module_name, os.path.abspath(path_to_file))
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


def import_app_main(app_name, path=None):
    """Dynamically imports the main function of an App.
    
    Args:
        app_name (str): The name of the App from which to import the main function.
        path (str, optional): The path to the apps module. Defaults to core.config.paths.apps_path

    Returns:
        The module object that was imported.
    """
    if path is None:
        path = core.config.paths.apps_path
    app_path = os.path.join(path, app_name, 'main.py')
    module_name = construct_module_name_from_path(app_path[:-3])
    try:
        return sys.modules[module_name]
    except KeyError:
        pass
    try:
        imported_module = import_py_file(module_name, app_path)
        sys.modules[module_name] = imported_module
        return imported_module
    except (ImportError, IOError, OSError) as e:
        logger.error('Cannot load app main for app {0}. Error: {1}'.format(app_name, e))
        pass


def __list_valid_directories(path):
    try:
        return [f for f in os.listdir(path)
                if (os.path.isdir(os.path.join(path, f))
                    and not f.startswith('__'))]
    except (IOError, OSError) as e:
        logger.error('Cannot get valid directories inside {0}. Error: {1}'.format(path, e))
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

from connexion.lifecycle import ConnexionResponse

def responseDecorator(func):
    def __wrapper(*args, **kwargs):
        body = func(*args, **kwargs)
        r = ConnexionResponse(body=body)
        return r
    return __wrapper

def load_app_function(app_instance, function_name):
    """Get a function for an App.
    
    Args:
        app_instance (App): An instance of the App object from which to load the function.
        function_name (str): The name of the function to be loaded from the App.
        
    Returns:
        The specified function if the attribute exists, otherwise None.
    """

    try:
        key = "Main." + function_name
        if key in app_instance.api.operations:
            obj = app_instance.api.operations[key]
            fn = obj.function
            return fn
        return None
    except AttributeError:
        logger.error('Could not load action {0} in app {1}.'.format(app_instance.name, function_name))
        return None


def load_flag_function(api, function_name):
    """Get a function for an App.

    Args:
        app_instance (App): An instance of the App object from which to load the function.
        function_name (str): The name of the function to be loaded from the App.

    Returns:
        The specified function if the attribute exists, otherwise None.
    """

    try:
        key = function_name
        if "execute" in api.operations:
            obj = api.operations["execute"]
            fn = obj.function
            return fn
        return None
    except AttributeError:
        logger.error('Could not load action {0} in app {1}.'.format(api.name, function_name))
        return None

def locate_workflows_in_directory(path=None):
    """Get a list of workflows in a specified directory or the workflows_path directory as specified in the configuration.
    
    Args:
        path (str, optional): The directory path from which to locate the workflows. Defaults to None.
        
    Returns:
        A list of workflow names from the specified path, or the directory specified in the configuration.
    """
    path = path if path is not None else core.config.paths.workflows_path
    if os.path.exists(path):
        return [workflow for workflow in os.listdir(path) if (os.path.isfile(os.path.join(path, workflow))
                                                              and workflow.endswith('.workflow'))]
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
        tree = ElementTree.ElementTree(file=filename)
        return [workflow.get('name') for workflow in tree.iter(tag="workflow")]


__workflow_key_separator = '-'


def construct_workflow_name_key(playbook, workflow):
    """Constructs a key for the workflow given the playbook name and workflow name.
    
    Args:
        playbook (str): The playbook under which the workflow is located.
        workflow (str): The name of the workflow.
        
    Returns:
        The key for the workflow given the playbook name and workflow name.
    """
    return '{0}{1}{2}'.format(playbook.lstrip(__workflow_key_separator), __workflow_key_separator, workflow)


def extract_workflow_name(workflow_key, playbook_name=''):
    """Extracts a workflow name from a given key.
    
    Args:
        workflow_key (str): The constructed key of the workflow from the playbook name and workflow name.
        playbook_name (str, optional): The playbook under which the workflow is located.
        
    Returns:
        The extracted workflow name.
    """
    if playbook_name and workflow_key.startswith(playbook_name):
        return workflow_key[len('{0}{1}'.format(playbook_name, __workflow_key_separator)):]
    else:
        return __workflow_key_separator.join(workflow_key.split(__workflow_key_separator)[1:])


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
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_package in pkgutil.walk_packages(package.__path__):
        full_name = '{0}.{1}'.format(package.__name__, name)
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_package:
            results.update(import_submodules(full_name))
    return results


class SubclassRegistry(type):
    """
    Metaclass which registers its subclasses in a dict of {name: cls}
    """
    def __init__(cls, name, bases, nmspc):
        super(SubclassRegistry, cls).__init__(name, bases, nmspc)
        if not hasattr(cls, 'registry'):
            cls.registry = dict()
        cls.registry[name] = cls


def format_db_path(db_type, path):
    return '{0}://{1}'.format(db_type, path) if db_type != 'sqlite' else '{0}:///{1}'.format(db_type, path)

from connexion.decorators import parameter
def formatarg(arg):
    if "format" in arg:
        format = arg["format"]
    elif "type" in arg:
        format = arg["type"]
    else:
        format = "str"

    if format == "str":
        f = "string"
    elif format == "int":
        f = "integer"
    elif format == "bool":
        f = "boolean"
    elif format == "obj":
        f = "object"
    elif format == "num":
        f = "number"
    elif format == "arr":
        f = "array"
    else:
        f = "string"

    arg["format"] = f

    if f == "array":
        itemFormat = formatarg(arg["items"])
        f = {"type": format, "items": {"type": itemFormat}}
    else:
        f = {"type":f}
    try:
        if "value" not in arg:
            arg["value"] = ""

        result = parameter.get_val_from_param(arg["value"], f)
        return result
    except Exception:
        raise ValueError


def arg_to_xml(arg):
    """Converts Argument object to XML

    Returns:
        XML of Argument object, or None if key is None.
    """
    if arg["key"]:
        elem = ElementTree.Element(arg["key"])
        if "value" in arg:
            elem.text = str(arg["value"])
        else:
            elem.text = ""
        if "format" in arg:
            format = arg["format"]
        else:
            format = "str"
        if 'items' in arg:
            format += ":" + arg["items"]
        elem.set("format", format)
        return elem
    else:
        return None


def action(func):
    """
    Decorator used to tag a method or function as an action

    Args:
        func (func): Function to tag
    Returns:
        (func) Tagged function
    """
    func.action = True  # tag the function as an action
    return func


def import_all_apps(path=None):
    for app_name in list_apps(path):
        import_app_main(app_name, path=path)
