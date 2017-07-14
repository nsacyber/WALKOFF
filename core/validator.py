import json
import logging
import os
from copy import deepcopy
from functools import partial

from connexion.utils import boolean
from jsonschema import RefResolver, draft4_format_checker, ValidationError
from jsonschema.validators import Draft4Validator
from six import string_types
from swagger_spec_validator import ref_validators
from swagger_spec_validator.validator20 import deref

import core.config.config
import core.config.paths
from core.helpers import InvalidInput, get_function_arg_names, InvalidApi, format_exception_message

logger = logging.getLogger(__name__)

TYPE_MAP = {
    'integer': int,
    'number': float,
    'boolean': boolean,
    'string': str
}

reserved_return_codes = ['UnhandledException', 'InvalidInput', 'EventTimedOut']

def make_type(value, type_literal):
    type_func = TYPE_MAP.get(type_literal)
    if (isinstance(value, dict) or isinstance(value, list)) and type_func == str:
        return json.dumps(value)
    else:
        return type_func(value)


def convert_primitive_type(value, parameter_type):
    return make_type(value, parameter_type)


def convert_primitive_array(values, parameter_type):
    return [convert_primitive_type(value, parameter_type) for value in values]


def convert_array(schema, param_in, message_prefix):
    if 'items' not in schema:
        return param_in
    item_type = schema['items']['type']
    if item_type in TYPE_MAP:
        try:
            return convert_primitive_array(param_in, item_type)
        except ValueError:
            items = str(param_in)
            items = items if len(items) < 30 else '{0}...]'.format(items[:30])
            message = '{0} has invalid input. Input {1} could not be converted to array ' \
                      'with type "object"'.format(message_prefix, items)
            logger.error(message)
            raise InvalidInput(message)
    else:
        return [convert_json(schema['items'], param, message_prefix) for param in param_in]


def __convert_json(schema, param_in, message_prefix):
    if not isinstance(param_in, dict):
        raise InvalidInput(
            '{0} A JSON object was expected. '
            'Instead got "{1}" of type {2}.'.format(message_prefix, param_in, type(param_in).__name__))
    if 'properties' not in schema:
        return param_in
    ret = {}
    for param_name, param_value in param_in.items():
        if param_name in schema['properties']:
            ret[param_name] = convert_json(schema['properties'][param_name], param_value, message_prefix)
        else:
            raise InvalidInput('{0} Input has unknown parameter {1}'.format(message_prefix, param_name))
    return ret


def convert_json(spec, param_in, message_prefix):
    if 'type' in spec:
        parameter_type = spec['type']
        if parameter_type in TYPE_MAP:
            try:
                return convert_primitive_type(param_in, parameter_type)
            except ValueError:
                message = (
                    '{0} has invalid input. '
                    'Input {1} could not be converted to type {2}'.format(message_prefix, param_in, parameter_type))
                logger.error(message)
                raise InvalidInput(message)
        elif parameter_type == 'array':
            return convert_array(spec, param_in, message_prefix)
        elif parameter_type == 'object':
            return __convert_json(spec, param_in, message_prefix)
        else:
            raise InvalidApi('{0} has invalid api'.format(message_prefix))
    elif 'schema' in spec:
        return convert_json(spec['schema'], param_in, message_prefix)
    else:
        raise InvalidApi('{0} has invalid api'.format(message_prefix))


def validate_app_spec(spec, app_name, spec_url='', http_handlers=None):
    walkoff_resolver = validate_spec_json(
        spec,
        os.path.join(core.config.paths.walkoff_schema_path),
        spec_url,
        http_handlers)
    dereference = partial(deref, resolver=walkoff_resolver)
    dereferenced_spec = dereference(spec)
    actions = dereference(dereferenced_spec['actions'])
    definitions = dereference(dereferenced_spec.get('definitions', {}))
    validate_actions(actions, dereference, app_name)
    validate_definitions(definitions, dereference)


def validate_flagfilter_spec(spec, spec_url='', http_handlers=None):
    walkoff_resolver = validate_spec_json(
        spec,
        os.path.join(core.config.paths.walkoff_schema_path),
        spec_url,
        http_handlers)
    dereference = partial(deref, resolver=walkoff_resolver)
    dereferenced_spec = dereference(spec)
    flag_spec = dereference(dereferenced_spec['flags'])
    filter_spec = dereference(dereferenced_spec['filters'])
    validate_flagfilter_params(flag_spec, 'Flag', core.config.config.flags, dereference)
    validate_flagfilter_params(filter_spec, 'Filter', core.config.config.filters, dereference)


def validate_data_in_param(params, data_in_param_name, message_prefix):
    data_in_param = next((param for param in params if param['name'] == data_in_param_name), None)
    if data_in_param is None:
        raise InvalidApi(
            '{0} has a dataIn param {1} '
            'for which it does not have a '
            'corresponding parameter'.format(message_prefix, data_in_param_name))
    elif not data_in_param.get('required', False):
        raise InvalidApi(
            '{0} has a dataIn param {1} which is not marked as required in the api. '
            'Add "required: true" to parameter specification for {1}'.format(message_prefix,
                                                                             data_in_param_name))


def validate_flagfilter_params(spec, action_type, defined_actions, dereferencer):
    seen = set()
    for action_name, action in spec.items():
        action = dereferencer(action)
        action_params = dereferencer(action.get('parameters', []))
        if action['run'] not in defined_actions:
            raise InvalidApi('{0} action {1} has a "run" param {2} '
                             'which is not defined'.format(action_type, action_name, action['run']))

        data_in_param_name = action['dataIn']
        validate_data_in_param(action_params, data_in_param_name, '{0} action {1}'.format(action_type, action_name))
        validate_action_params(action_params, dereferencer, action_type, action_name, defined_actions[action['run']])
        seen.add(action['run'])

    if seen != set(defined_actions.keys()):
        logger.warning('Global {0}s have defined the following actions which do not have a corresponding API: '
                       '{1}'.format(action_type.lower(), (set(defined_actions.keys()) - seen)))


def validate_spec_json(spec, schema_path, spec_url='', http_handlers=None):
    schema_path = os.path.abspath(schema_path)
    with open(schema_path, 'r') as schema_file:
        schema = json.loads(schema_file.read())
    schema_resolver = RefResolver('file://{}'.format(schema_path), schema)
    spec_resolver = RefResolver(spec_url, spec, handlers=http_handlers or {})

    ref_validators.validate(spec,
                            schema,
                            resolver=schema_resolver,
                            instance_cls=ref_validators.create_dereffing_validator(spec_resolver),
                            cls=Draft4Validator)
    return spec_resolver


def validate_actions(actions, dereferencer, app_name):
    from apps import get_all_actions_for_app, get_app_action
    defined_actions = get_all_actions_for_app(app_name)
    seen = set()
    for action_name, action in actions.items():
        if action['run'] not in defined_actions:
            raise InvalidApi('Action {0} has "run" property {1} '
                             'which is not defined in App {2}'.format(action_name, action['run'], app_name))
        action = dereferencer(action)
        action_params = dereferencer(action.get('parameters', []))
        event = action.get('event', '')
        if action_params:
            validate_action_params(action_params, dereferencer, app_name,
                                   action_name, get_app_action(app_name, action['run']), event=event)
        validate_app_action_return_codes(action.get('returns', []), app_name, action_name)
        seen.add(action['run'])
    if seen != set(defined_actions.keys()):
        logger.warning('App {0} has defined the following actions which do not have a corresponding API: '
                       '{1}'.format(app_name, (set(defined_actions.keys()) - seen)))


def validate_action_params(parameters, dereferencer, app_name, action_name, action_func, event=''):
    seen = set()
    for parameter in parameters:
        parameter = deref(parameter, dereferencer)
        name = parameter['name']
        if name in seen:
            raise InvalidApi('Duplicate parameter {0} in api for {1} '
                             'for action {2}'.format(name, app_name, action_name))
        seen.add(name)

    if hasattr(action_func, '__arg_names'):
        method_params = action_func.__arg_names
    else:
        method_params = get_function_arg_names(action_func)

    if method_params and method_params[0] == 'self':
        method_params.pop(0)

    if event:
        method_params.pop(0)

        if action_func.__event_name != event:
            logger.warning('In app {0} action {1}, event documented {2} does not match '
                           'event specified {3}'.format(app_name, action_name, event, action_func.__event_name))

    if not seen == set(method_params):
        only_in_api = seen - set(method_params)
        only_in_definition = set(method_params) - seen
        message = ('Discrepancy between defined parameters in API and in method definition '
                   'for app {0} action {1}.'.format(app_name, action_name))
        if only_in_api:
            message += ' Only in API: {0}.'.format(only_in_api)
        if only_in_definition:
            message += ' Only in definition: {0}'.format(only_in_definition)
        raise InvalidApi(message)


def validate_app_action_return_codes(return_codes, app, action):
    reserved = [return_code for return_code in return_codes if return_code in reserved_return_codes]
    if reserved:
        message = 'App {0} action {1} has return codes {2} which are reserved'.format(app, action, reserved)
        logger.error(message)
        raise InvalidApi(message)


def validate_definition(definition, dereferencer, definition_name=None):
    definition = dereferencer(definition)

    if 'allOf' in definition:
        for inner_definition in definition['allOf']:
            validate_definition(inner_definition, dereferencer)
    else:
        required = definition.get('required', [])
        properties = definition.get('properties', {}).keys()
        extra_properties = list(set(required) - set(properties))
        if extra_properties:
            raise InvalidApi("Required list of properties for definition "
                             "{0} not defined: {1}".format(definition_name, extra_properties))


def validate_definitions(definitions, dereferencer):
    for definition_name, definition in definitions.items():
        validate_definition(definition, dereferencer, definition_name)


def validate_primitive_parameter(value, param, parameter_type, message_prefix):
    try:
        converted_value = convert_primitive_type(value, parameter_type)
    except (ValueError, TypeError):
        message = '{0} has invalid input. ' \
                  'Input {1} could not be converted to type {2}'.format(message_prefix, value, parameter_type)
        logger.error(message)
        raise InvalidInput(message)
    else:
        param = deepcopy(param)
        if 'required' in param:
            del param['required']
        try:
            Draft4Validator(
                param, format_checker=draft4_format_checker).validate(converted_value)
        except ValidationError as exception:
            message = '{0} has invalid input. ' \
                      'Input {1} with type {2} does not conform to ' \
                      'validators: {3}'.format(message_prefix, value, parameter_type,
                                               format_exception_message(exception))
            logger.error(message)
            raise InvalidInput(message)
        return converted_value


def validate_parameter(value, param, message_prefix):
    primitive_type = 'primitive' if 'type' in param else 'object'
    converted_value = None
    if value is not None:
        if primitive_type == 'primitive':
            primitive_type = param['type']
            if primitive_type in TYPE_MAP:
                converted_value = validate_primitive_parameter(value, param, primitive_type, message_prefix)
            elif primitive_type == 'array':
                try:
                    converted_value = convert_array(param, value, message_prefix)
                    Draft4Validator(
                        param, format_checker=draft4_format_checker).validate(converted_value)
                except ValidationError as exception:
                    message = '{0} has invalid input. Input {1} does not conform to ' \
                              'validators: {2}'.format(message_prefix, value, format_exception_message(exception))
                    logger.error(message)
                    raise InvalidInput(message)
            else:
                raise InvalidInput('In {0}: Unknown parameter type {1}'.format(message_prefix, primitive_type))
        else:
            try:
                converted_value = convert_json(param, value, message_prefix)
                Draft4Validator(
                    param['schema'], format_checker=draft4_format_checker).validate(converted_value)
            except ValidationError as exception:
                message = '{0} has invalid input. Input {1} does not conform to ' \
                          'validators: {2}'.format(message_prefix, value, format_exception_message(exception))
                logger.error(message)
                raise InvalidInput(message)
    elif param.get('required'):
        message = "In {0}: Missing {1} parameter '{2}'".format(message_prefix, primitive_type, param['name'])
        logger.error(message)
        raise InvalidInput(message)

    return converted_value


def validate_parameters(api, inputs, message_prefix):
    api_dict = {}
    for param in api:
        api_dict[param['name']] = param
    converted = {}
    seen_params = set()
    input_set = set(inputs.keys())
    for param_name, param_api in api_dict.items():
        if param_name in inputs:
            if not isinstance(inputs[param_name], string_types):
                converted[param_name] = validate_parameter(inputs[param_name], param_api, message_prefix)
            else:
                if inputs[param_name].startswith('@'):
                    converted[param_name] = inputs[param_name]
                elif inputs[param_name].startswith('\@'):
                    inputs[param_name] = inputs[param_name][1:]
                    converted[param_name] = validate_parameter(inputs[param_name], param_api, message_prefix)
                else:
                    converted[param_name] = validate_parameter(inputs[param_name], param_api, message_prefix)
        elif 'default' in param_api:
            try:
                default_param = validate_parameter(param_api['default'], param_api, message_prefix)
            except InvalidInput as e:
                default_param = param_api['default']
                logger.warning(
                    'For {0}: Default input {1} (value {2}) does not conform to schema. (Error: {3})'
                    'Using anyways'.format(message_prefix, param_name, param_api['default'], format_exception_message(e)))

            converted[param_name] = default_param
            input_set.add(param_name)
        elif 'required' in param_api:
            message = 'For {0}: Parameter {1} is not specified and has no default'.format(message_prefix, param_name)
            logger.error(message)
            raise InvalidInput(message)
        else:
            converted[param_name] = None
            input_set.add(param_name)
        seen_params.add(param_name)
    if seen_params != input_set:
        message = 'For {0}: Too many inputs. Extra inputs: {1}'.format(message_prefix, input_set - seen_params)
        logger.error(message)
        raise InvalidInput(message)
    return converted


def validate_app_action_parameters(api, inputs, app, action):
    message_prefix = 'app {0} action {1}'.format(app, action)
    return validate_parameters(api, inputs, message_prefix)


def validate_flag_parameters(api, inputs, flag):
    return validate_parameters(api, inputs, 'flag {0}'.format(flag))


def validate_filter_parameters(api, inputs, filter_name):
    return validate_parameters(api, inputs, 'filter {0}'.format(filter_name))
