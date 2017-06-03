from connexion.decorators.validation import make_type
from swagger_spec_validator.validator20 import deref
from swagger_spec_validator import ref_validators
from functools import partial
import os
import json
from jsonschema import RefResolver
from jsonschema.validators import Draft4Validator
from apps import get_all_actions_for_app, get_app_action
import sys
import logging

logger = logging.getLogger(__name__)

__new_inspection = False
if sys.version_info.major >= 3 and sys.version_info.minor >= 3:
    from inspect import signature as getsignature
    __new_inspection = True
else:
    from inspect import getargspec as getsignature


class InvalidAppApi(Exception):
    pass


def convert_primitive_type(value, parameter_type):
    make_type(value, parameter_type)


def convert_primitive_array(values, parameter_type):
    return [convert_primitive_type(value, parameter_type) for value in values]


def validate_spec(spec, app_name, spec_url='', http_handlers=None):
    walkoff_resolver = validate_spec_json(
        spec,
        os.path.join('core', 'schemas', 'new_schema.json'),
        spec_url,
        http_handlers)
    dereference = partial(deref, resolver=walkoff_resolver)
    dereferenced_spec = dereference(spec)
    actions = dereference(dereferenced_spec['actions'])
    definitions = dereference(dereferenced_spec.get('definitions', {}))
    validate_actions(actions, dereference, app_name)
    validate_definitions(definitions, dereference)


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
    defined_actions = get_all_actions_for_app(app_name)
    seen = set()
    for action_name, action in actions.items():
        if action['run'] not in defined_actions:
            raise InvalidAppApi('Action {0} has "run" property {1} '
                                'which is not defined in App {2}'.format(action_name, action['run'], app_name))
        action = dereferencer(action)
        action_params = dereferencer(action.get('parameters', []))
        if action_params:
            validate_action_params(action_params, dereferencer, app_name, action_name, action['run'])
        seen.add(action['run'])
    if seen != set(defined_actions.keys()):
        logger.warning('App {0} has defined the following actions which do not have a corresponding API: '
                       '{1}'.format(app_name, (set(defined_actions.keys()) - seen)))


def validate_action_params(parameters, dereferencer, app_name, action_name, run):
    seen = set()
    for parameter in parameters:
        parameter = deref(parameter, dereferencer)
        name = parameter['name']
        if name in seen:
            raise InvalidAppApi('Duplicate parameter {0} in api for app {1} '
                                'for action {2}'.format(name, app_name, action_name))
        seen.add(name)

    app_action = get_app_action(app_name, run)
    if __new_inspection:
        method_params = list(getsignature(app_action).parameters.keys())
    else:
        method_params = getsignature(app_action).args  # pre-inspect the function to get its arguments
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