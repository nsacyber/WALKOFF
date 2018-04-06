import importlib
import json
import logging
import os
import pkgutil
import sys
import warnings
from datetime import datetime
from uuid import uuid4



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


def list_valid_directories(path):
    try:
        return [f for f in os.listdir(path)
                if (os.path.isdir(os.path.join(path, f))
                    and not f.startswith('__'))]
    except (IOError, OSError) as e:
        logger.error('Cannot get valid directories inside {0}. Error: {1}'.format(path, format_exception_message(e)))
        return []


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
    if db_type != 'sqlite':
        sep = '//'
    else:
        if os.name == 'nt':
            sep = '///'
        elif os.name == 'posix':
            sep = '////'
        path = os.path.abspath(path)

    return '{0}:{1}{2}'.format(db_type, sep, path)


class InvalidExecutionElement(Exception):
    def __init__(self, id_, name, message, errors=None):
        self.id = id_
        self.name = name
        self.errors = errors or {}
        super(InvalidExecutionElement, self).__init__(message)


def get_function_arg_names(func):
    if __new_inspection:
        return list(getsignature(func).parameters.keys())
    else:
        return getsignature(func).args


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
    warnings.warn('create_sse_event is deprecated. Please use the walkoff.sse.SseStream class to construct SSE streams.'
                  ' This function will be removed in version 0.10.0',
                  DeprecationWarning)
    if data is None and event_id is None and event is None:
        return ''
    response = ''
    if event_id is not None:
        response += 'id: {}\n'.format(event_id)
    if event is not None:
        response += 'event: {}\n'.format(event)
    if data is None:
        data = ''
    try:
        response += 'data: {}\n'.format(json.dumps(data))
    except ValueError:
        response += 'data: {}\n'.format(data)
    return response + '\n'


def regenerate_workflow_ids(workflow):
    workflow['id'] = str(uuid4())
    action_mapping = {}
    actions = workflow.get('actions', [])
    for action in actions:
        prev_id = action['id']
        action['id'] = str(uuid4())
        action_mapping[prev_id] = action['id']

    for action in actions:
        regenerate_ids(action, action_mapping, False)

    for branch in workflow.get('branches', []):
        branch['source_id'] = action_mapping[branch['source_id']]
        branch['destination_id'] = action_mapping[branch['destination_id']]
        regenerate_ids(branch, action_mapping)

    workflow['start'] = action_mapping[workflow['start']]


def regenerate_ids(json_in, action_mapping=None, regenerate_id=True, is_arguments=False):
    if regenerate_id:
        json_in['id'] = str(uuid4())
    if is_arguments:
        json_in.pop('id', None)

    if 'reference' in json_in and json_in['reference']:
        json_in['reference'] = action_mapping[json_in['reference']]

    for field, value in json_in.items():
        if isinstance(value, list):
            is_arguments = field == 'arguments'
            __regenerate_ids_of_list(value, action_mapping, is_arguments=is_arguments)
        elif isinstance(value, dict):
            regenerate_ids(value, action_mapping=action_mapping)


def __regenerate_ids_of_list(value, action_mapping, is_arguments=False):
    for list_element in (list_element_ for list_element_ in value
                         if isinstance(list_element_, dict)):
        regenerate_ids(list_element, action_mapping=action_mapping, is_arguments=is_arguments)


def utc_as_rfc_datetime(timestamp):
    return timestamp.isoformat('T') + 'Z'


def timestamp_to_datetime(time):
    return datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ')


def json_dumps_or_string(val):
    try:
        return json.dumps(val)
    except (ValueError, TypeError):
        return str(val)
