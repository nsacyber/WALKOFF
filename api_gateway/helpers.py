import importlib
import json
import logging
import os
import pkgutil
import sys
import warnings
from datetime import datetime
from uuid import uuid4, UUID

from importlib import reload as reload_module
from inspect import signature as getsignature

logger = logging.getLogger(__name__)


def __list_valid_directories(path):
    try:
        return [f for f in os.listdir(path)
                if (os.path.isdir(os.path.join(path, f))
                    and not f.startswith('__'))]
    except (IOError, OSError) as e:
        logger.error('Cannot get valid directories inside {0}. Error: {1}'.format(path, format_exception_message(e)))
        return []


def list_apps(path):
    """Get a list of the apps.

    Args:
        path (str): The path to the apps folder

    Returns:
        A list of the apps given the apps path or the apps_path in the configuration.
    """
    return __list_valid_directories(path)


# def list_interfaces(path=None):
#     return __list_valid_directories(path)


# def locate_playbooks_in_directory(path):
#     """Get a list of workflows in a specified directory or the workflows_path directory as specified in the configuration.
#
#     Args:
#         path (str, optional): The directory path from which to locate the workflows.
#
#     Returns:
#         A list of workflow names from the specified path, or the directory specified in the configuration.
#     """
#     if os.path.exists(path):
#         return [workflow for workflow in os.listdir(path) if (os.path.isfile(os.path.join(path, workflow))
#                                                               and workflow.endswith('.playbook'))]
#     else:
#         logger.warning('Could not locate any workflows in directory {0}. Directory does not exist'.format(path))
#         return []


# def import_submodules(package, recursive=False):
#     """Imports the submodules from a given package.
#
#     Args:
#         package (str): The name of the package from which to import the submodules.
#         recursive (bool, optional): A boolean to determine whether or not to recursively load the submodules.
#             Defaults to False.
#
#     Returns:
#         A dictionary containing the imported module objects.
#     """
#     successful_base_import = True
#     if isinstance(package, str):
#         try:
#             package = importlib.import_module(package)
#         except ImportError:
#             successful_base_import = False
#             logger.warning('Could not import {}. Skipping'.format(package), exc_info=True)
#     if successful_base_import:
#         results = {}
#         if hasattr(package, '__path__'):
#             for loader, name, is_package in pkgutil.walk_packages(package.__path__):
#                 full_name = '{0}.{1}'.format(package.__name__, name)
#                 try:
#                     results[full_name] = importlib.import_module(full_name)
#                 except ImportError:
#                     logger.warning('Could not import {}. Skipping.'.format(full_name), exc_info=True)
#                 if recursive and is_package:
#                     results.update(import_submodules(full_name))
#         return results
#     return {}


def format_db_path(db_type, path, username_env_key=None, password_env_key=None, host="localhost"):
    """
    Formats the path to the database

    Args:
        db_type (str): Type of database being used
        path (str): Path to the database
        username_env_key (str): The name of the username environment variable for this db
        password_env_key (str): The name of the password environment variable for this db
        host (str): The hostname where the database is hosted
    Returns:
        (str): The path of the database formatted for SqlAlchemy
    """
    supported_dbs = ['postgresql', 'postgresql+psycopg2', 'postgresql+pg8000',
                     'mysql', 'mysql+mysqldb', 'mysql+mysqlconnector', 'mysql+oursql',
                     'oracle', 'oracle+cx_oracle', 'mssql+pyodbc', 'mssql+pymssql']
    sqlalchemy_path = None

    if db_type == 'sqlite':
        sqlalchemy_path = f"{db_type}:///{path}"

    elif db_type in supported_dbs:
        username = os.environ.get(username_env_key, None)
        password = os.environ.get(password_env_key, None)

        if username and password:
            sqlalchemy_path = f"{db_type}://{username}:{password}@{host}/{path}"
        elif username:
            sqlalchemy_path = f"{db_type}://{username}@{host}/{path}"
        else:
            logger.error(f"Database type was set to {db_type}, but no login was found in system environment variables.")

    else:
        logger.error(f"Database type {db_type} not supported for database {path}")

    return sqlalchemy_path


def get_function_arg_names(func):
    return list(getsignature(func).parameters.keys())


def format_exception_message(exception):
    exception_message = str(exception)
    class_name = exception.__class__.__name__
    return f"{class_name}: {exception_message}" if exception_message else class_name


def convert_action_argument(argument):
    if 'value' in argument:
        try:
            argument['value'] = json.loads(argument['value'])
        except ValueError:
            pass
    if 'selection' in argument:
        tmp = []
        for arg in argument['selection']:
            tmp.append(convert_action_argument(arg))
        argument['selection'] = tmp
    return argument


# def create_sse_event(event_id=None, event=None, data=None):
#     warnings.warn('create_sse_event is deprecated.'
#                   ' Please use the api_gateway.sse.SseStream class to construct SSE streams.'
#                   ' This function will be removed in version 0.10.0',
#                   DeprecationWarning)
#     if data is None and event_id is None and event is None:
#         return ''
#     response = ''
#     if event_id is not None:
#         response += 'id: {}\n'.format(event_id)
#     if event is not None:
#         response += 'event: {}\n'.format(event)
#     if data is None:
#         data = ''
#     try:
#         response += 'data: {}\n'.format(json.dumps(data))
#     except ValueError:
#         response += 'data: {}\n'.format(data)
#     return response + '\n'


def regenerate_workflow_ids(workflow):
    workflow['id_'] = str(uuid4())
    id_mapping = {}
    actions = workflow.get('actions', [])
    for action in actions:
        prev_id = action['id_']
        action['id_'] = str(uuid4())
        id_mapping[prev_id] = action['id_']

    conditions = workflow.get('conditions', [])
    for condition in conditions:
        prev_id = condition['id_']
        condition['id_'] = str(uuid4())
        id_mapping[prev_id] = condition['id_']

    transforms = workflow.get('transforms', [])
    for transform in transforms:
        prev_id = transform['id_']
        transform['id_'] = str(uuid4())
        id_mapping[prev_id] = transform['id_']

    workflow_variables = workflow.get('workflow_variables', [])
    for workflow_variable in workflow_variables:
        prev_id = workflow_variable["id_"]
        workflow_variable['id_'] = str(uuid4())
        id_mapping[prev_id] = workflow_variable['id_']

    for action in actions:
        regenerate_ids(action, id_mapping, regenerate_id=False)

    # ToDo: These will be needed if condition/transform parameters are changed to be more like actions
    # for condition in conditions:
    #     regenerate_ids(condition, id_mapping, regenerate_id=False)
    #
    # for transform in transforms:
    #     regenerate_ids(transform, id_mapping, regenerate_id=False)

    for branch in workflow.get('branches', []):
        branch['source_id'] = id_mapping[branch['source_id']]
        branch['destination_id'] = id_mapping[branch['destination_id']]
        regenerate_ids(branch, id_mapping)

    workflow['start'] = id_mapping[workflow['start']]


def regenerate_ids(json_in, id_mapping=None, regenerate_id=True, is_arguments=False):
    if regenerate_id:
        json_in['id_'] = str(uuid4())
    if is_arguments:
        json_in.pop('id_', None)

    if json_in.get('variant') in ("ACTION_RESULT", "WORKFLOW_VARIABLE"):
        json_in['value'] = id_mapping[json_in['value']]

    for field, value in json_in.items():
        is_arguments = field in ['arguments', 'device_id']
        if isinstance(value, list):
            __regenerate_ids_of_list(value, id_mapping, is_arguments=is_arguments)
        elif isinstance(value, dict):
            regenerate_ids(value, id_mapping=id_mapping, is_arguments=is_arguments)


def __regenerate_ids_of_list(value, id_mapping, is_arguments=False):
    for list_element in (list_element_ for list_element_ in value
                         if isinstance(list_element_, dict)):
        regenerate_ids(list_element, id_mapping=id_mapping, is_arguments=is_arguments)


# def strip_device_ids(workflow):
#     for action in workflow.get('actions', []):
#         action.pop('device_id', None)
#
#
# def strip_argument_ids(workflow):
#     for action in workflow.get('actions', []):
#         strip_argument_ids_from_element(action)
#         if 'device_id' in action:
#             action['device_id'].pop('id_', None)
#
#
# def strip_argument_ids_from_conditional(conditional):
#     for conditional_expression in conditional.get('child_expressions', []):
#         strip_argument_ids_from_conditional(conditional_expression)
#     for condition in conditional.get('conditions', []):
#         strip_argument_ids_from_element(condition)
#         for transform in condition.get('transforms', []):
#             strip_argument_ids_from_element(transform)
#
#
# def strip_argument_ids_from_element(element):
#     for argument in element.get('arguments', []):
#         argument.pop('id_', None)


def utc_as_rfc_datetime(timestamp):
    return timestamp.isoformat('T') + 'Z'


def timestamp_to_datetime(time):
    return datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ')


def json_dumps_or_string(val):
    try:
        return json.dumps(val)
    except (ValueError, TypeError):
        return str(val)


def read_and_indent(filename, indent):
    indent = '  ' * indent
    with open(filename, 'r') as file_open:
        return [f'{indent}{line}' for line in file_open]


def validate_uuid4(id_, stringify=False):
    try:
        uuid_ = UUID(id_, version=4)
        return uuid_ if not stringify else id_
    except (ValueError, TypeError):
        return None


def compose_api(config):
    with open(os.path.join(config.API_PATH, 'api.yaml'), 'r') as api_yaml:
        final_yaml = []
        for line_num, line in enumerate(api_yaml):
            if line.lstrip().startswith('$ref:'):
                split_line = line.split('$ref:')
                reference = split_line[1].strip()
                indentation = split_line[0].count('  ')
                try:
                    final_yaml.extend(
                        read_and_indent(os.path.join(config.API_PATH, reference), indentation))
                    final_yaml.append(os.linesep)
                except (IOError, OSError):
                    logger.error(f"Could not find or open {reference} on line {line_num}")
            else:
                final_yaml.append(line)
    with open(os.path.join(config.API_PATH, 'composed_api.yaml'), 'w') as composed_yaml:
        composed_yaml.writelines(final_yaml)


class ExecutionError(Exception):
    def __init__(self, original_exception=None, message=None):
        if original_exception is None and message is None:
            raise ValueError('Either original exception or message must be provided')
        self.exc = original_exception or None
        self.message = message or format_exception_message(original_exception)
        super(ExecutionError, self).__init__()
