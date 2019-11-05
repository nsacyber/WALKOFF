import json
import logging
import os
from datetime import datetime
from inspect import signature as getsignature
from uuid import uuid4

logger = logging.getLogger("API")


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


def sse_format(data, event_id, event=None, retry=None):
    """Get this SSE formatted as needed to send to the client
    Args:
        event_id (int): The ID related to this event.
        retry (int): The time in milliseconds the client should wait to retry to connect to this SSE stream if the
            connection is broken. Default is 3 seconds (3000 milliseconds)
    Returns:
        (str): This SSE formatted to be sent to the client
    """
    if isinstance(data, dict):
        try:
            data = json.dumps(data)
        except TypeError:
            data = str(data)

    formatted = 'id: {}\n'.format(event_id)
    if event:
        formatted += 'event: {}\n'.format(event)
    if retry is not None:
        formatted += 'retry: {}\n'.format(retry)
    if data:
        formatted += 'data: {}\n'.format(data)
    return formatted + '\n'


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
        for param in workflow.get('parameters', []):
            param['id_'] = str(uuid4())

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

    triggers = workflow.get('triggers', [])
    for trigger in triggers:
        prev_id = trigger['id_']
        trigger['id_'] = str(uuid4())
        id_mapping[prev_id] = trigger['id_']

    workflow_variables = workflow.get('workflow_variables', [])
    for workflow_variable in workflow_variables:
        prev_id = workflow_variable["id_"]
        workflow_variable['id_'] = str(uuid4())
        id_mapping[prev_id] = workflow_variable['id_']

    tags = workflow.get('tags', [])
    id_mapping["tags"] = tags

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


def compose_api(static):
    with open(os.path.join(static.API_PATH, 'api.yaml'), 'r') as api_yaml:
        final_yaml = []
        for line_num, line in enumerate(api_yaml):
            if line.lstrip().startswith('$ref:'):
                split_line = line.split('$ref:')
                reference = split_line[1].strip()
                indentation = split_line[0].count('  ')
                try:
                    final_yaml.extend(
                        read_and_indent(os.path.join(static.API_PATH, reference), indentation))
                    final_yaml.append(os.linesep)
                except (IOError, OSError):
                    logger.error(f"Could not find or open {reference} on line {line_num}")
            else:
                final_yaml.append(line)
    with open(os.path.join(static.API_PATH, 'composed_api.yaml'), 'w') as composed_yaml:
        composed_yaml.writelines(final_yaml)
        logger.info("Wrote composed_api.yaml")


class ExecutionError(Exception):
    def __init__(self, original_exception=None, message=None):
        if original_exception is None and message is None:
            raise ValueError('Either original exception or message must be provided')
        self.exc = original_exception or None
        self.message = message or format_exception_message(original_exception)
        super(ExecutionError, self).__init__()


class JSONOrString:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if type(v) == str:
            return v
        else:
            try:
                json.dumps(v)
            except (ValueError, TypeError):
                raise ValueError(f"JSONOrString: value is not a string or JSON serializable: {v}")
            else:
                return v
