from swagger_spec_validator.validator20 import deref
from swagger_spec_validator import ref_validators
from functools import partial
import os
import json
from copy import deepcopy
from jsonschema import RefResolver, draft4_format_checker, ValidationError
from jsonschema.validators import Draft4Validator
from connexion.utils import boolean
import sys
import logging
logger = logging.getLogger(__name__)
from core.helpers import InvalidStepInput
import core.config.paths

__new_inspection = False
if sys.version_info.major >= 3 and sys.version_info.minor >= 3:
    from inspect import signature as getsignature
    __new_inspection = True
else:
    from inspect import getargspec as getsignature


class InvalidAppApi(Exception):
    pass

TYPE_MAP = {
    'integer': int,
    'number': float,
    'boolean': boolean,
    'string': str
}


def make_type(value, type_literal):
    type_func = TYPE_MAP.get(type_literal)
    return type_func(value)


def convert_primitive_type(value, parameter_type):
    return make_type(value, parameter_type)


def convert_primitive_array(values, parameter_type):
    return [convert_primitive_type(value, parameter_type) for value in values]


def validate_app_spec(spec, app_name, spec_url='', http_handlers=None):
    walkoff_resolver = validate_spec_json(
        spec,
        os.path.join(core.config.paths.schema_path, 'new_schema.json'),
        spec_url,
        http_handlers)
    dereference = partial(deref, resolver=walkoff_resolver)
    dereferenced_spec = dereference(spec)
    actions = dereference(dereferenced_spec['actions'])
    definitions = dereference(dereferenced_spec.get('definitions', {}))
    validate_actions(actions, dereference, app_name)
    validate_definitions(definitions, dereference)


def validate_flagfilter_spec(spec, spec_url='', http_handlers=None):
    from core.config.config import flags, filters
    walkoff_resolver = validate_spec_json(
        spec,
        os.path.join(core.config.paths.schema_path, 'new_schema.json'),
        spec_url,
        http_handlers)
    dereference = partial(deref, resolver=walkoff_resolver)
    dereferenced_spec = dereference(spec)
    flag_spec = dereference(dereferenced_spec['flags'])
    filter_spec = dereference(dereferenced_spec['filters'])
    validate_flagfilter_params(flag_spec, 'Flag', flags, dereference)
    validate_flagfilter_params(filter_spec, 'Filter', filters, dereference)


def validate_flagfilter_params(spec, action_type, defined_actions, dereferencer):
    seen = set()
    for action_name, action in spec.items():
        action = dereferencer(action)
        action_params = dereferencer(action.get('parameters', []))
        if action['run'] not in defined_actions:
            raise InvalidAppApi('{0} action {1} has a "run" param {2} '
                                'which is not defined'.format(action_type, action_name, action['run']))

        data_in_param_name = action['dataIn']
        first = next((param for param in action_params if param['name'] == data_in_param_name), None)
        if first is None:
            raise InvalidAppApi(
                '{0} action {1} has a dataIn param {2} '
                'for which it does not have a '
                'corresponding parameter'.format(action_type, action_name, data_in_param_name))
        elif not first.get('required', False):
            raise InvalidAppApi(
                '{0} action {1} has a dataIn param {2} which is not marked as required in the api. '
                'Add "required: true" to parameter specification for {2}'.format(action_type, action_name,
                                                                                 data_in_param_name))

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
            raise InvalidAppApi('Action {0} has "run" property {1} '
                                'which is not defined in App {2}'.format(action_name, action['run'], app_name))
        action = dereferencer(action)
        action_params = dereferencer(action.get('parameters', []))
        if action_params:
            validate_action_params(action_params, dereferencer, app_name,
                                   action_name, get_app_action(app_name, action['run']))
        seen.add(action['run'])
    if seen != set(defined_actions.keys()):
        logger.warning('App {0} has defined the following actions which do not have a corresponding API: '
                       '{1}'.format(app_name, (set(defined_actions.keys()) - seen)))


def validate_action_params(parameters, dereferencer, app_name, action_name, action_func):
    seen = set()
    for parameter in parameters:
        parameter = deref(parameter, dereferencer)
        name = parameter['name']
        if name in seen:
            raise InvalidAppApi('Duplicate parameter {0} in api for {1} '
                                'for action {2}'.format(name, app_name, action_name))
        seen.add(name)

    if __new_inspection:
        method_params = list(getsignature(action_func).parameters.keys())
    else:
        method_params = getsignature(action_func).args  # pre-inspect the function to get its arguments
    if method_params and method_params[0] == 'self':
        method_params.pop(0)
    if not seen == set(method_params):
        only_in_api = seen - set(method_params)
        only_in_definition = set(method_params) - seen
        message = 'Discrepancy between defined parameters in API and in method definition.'
        if only_in_api:
            message += ' Only in API: {0}.'.format(only_in_api)
        if only_in_definition:
            message += ' Only in definition: {0}'.format(only_in_definition)
        raise InvalidAppApi(message)


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
            raise InvalidAppApi("Required list of properties for definition "
                                "{0} not defined: {1}".format(definition_name, extra_properties))


def validate_definitions(definitions, dereferencer):
    for definition_name, definition in definitions.items():
        validate_definition(definition, dereferencer, definition_name)


def validate_parameter(value, param, app, action):
    parameter_type = param['type']
    converted_value = None
    if value is not None:
        try:
            converted_value = convert_primitive_type(value, parameter_type)
        except ValueError as e:
            logger.error('Step with app {0} and action {1} has invalid input. '
                         'Input {2} could not be converted to type {3}'.format(app, action, value, parameter_type))
            raise InvalidStepInput(app, action, value=value, format_type=parameter_type)
        else:
            param = deepcopy(param)
            if 'required' in param:
                del param['required']
            try:
                Draft4Validator(
                    param, format_checker=draft4_format_checker).validate(converted_value)
            except ValidationError as exception:
                logger.error('Step with app {0} and action {1} has invalid input. '
                             'Input {2} with type {3} does not conform to '
                             'validators'.format(app, action, value, parameter_type))
                raise InvalidStepInput(app, action, value=converted_value, format_type=parameter_type)
    elif param.get('required'):
        logger.error("Missing {parameter_type} parameter '{param[name]}'".format(**locals()))
        raise InvalidStepInput(app, action)

    return converted_value


def validate_parameters(api, inputs, app, action):
    api_dict = {}
    for param in api:
        api_dict[param['name']] = param
    converted = {}
    seen_params = set()
    input_set = set(inputs.keys())
    for param_name, param_api in api_dict.items():
        if param_name in inputs:
            converted[param_name] = validate_parameter(inputs[param_name], param_api, app, action)
        elif 'default' in param_api:
            try:
                default_param = validate_parameter(param_api['default'], param_api, app, action)
            except InvalidStepInput:
                default_param = param_api['default']
                logger.warning('Default input {0} (value {1}) for app {2} action {3} does not conform to schema. '
                               'Using anyways'.format(param_name, param_api['default'], app, action))

            converted[param_name] = default_param
            input_set.add(param_name)
        else:
            logger.error('Parameter {0} for app {1} action {2} '
                         'is not specified and has no default'.format(param_name, app, action))
            raise InvalidStepInput(app, action)
        seen_params.add(param_name)
    if seen_params != input_set:
        logger.error('Too many inputs for app {0} action {1}. '
                     'Extra inputs: {2}'.format(app, action, input_set-seen_params))
        raise InvalidStepInput(app, action)
    return converted


"""
Pre-validation steps:
    1. Validate that the Walkoff conforms to the proper schema
        Done with simple JSON schema validation
    2. Replace references in the schema with actual reference. Validate if reference is malformed or not found
        Need to hijack swagger-spec-validator
    3. Validate that all the methods pointed to exist
        Can use the resolver from connexion
    4. Validate that the defaults are valid for the given type
        (Do not do. Could be useful to have non-conforming defaults)
        Can use connexion.operation.Operation.validate_defaults()
    <Any action which does not conform to the standards is not loaded into the metadata and cannot be used>

    5. Upon loading workflow, validate that all the apps and actions used exist
    6. Validate that the inputs to all the steps are valid (use Validator.validate_parameters)
    <Any workflow which is invalid is not loaded into the controller and cannot be used>

    7. When executing, validate that the previous step's output is valid for he given step
"""

"""
To do actual verification, should be done action by action:

"""