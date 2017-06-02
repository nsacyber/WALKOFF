from connexion.decorators.validation import make_type
from swagger_spec_validator.validator20 import deref
from swagger_spec_validator import ref_validators
from functools import partial
import os
import json
from jsonschema import RefResolver
from jsonschema.validators import Draft4Validator


class InvalidAppApi(Exception):
    pass


class InvalidAppStructure(Exception):
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
    for action_name, action in actions.items():
        action = dereferencer(action)
        action_params = dereferencer(action.get('parameters', []))
        if action_params:
            validate_action_params(action_params, dereferencer, app_name, action_name)
        # TODO: Validate that the actions in the 'run' are valid (should use registered actions)
        # TODO: Validate that the parameter names are same as parameters in API (use inspect module)


def validate_action_params(parameters, dereferencer, app_name, action_name):
    seen = set()
    for parameter in parameters:
        parameter = deref(parameter, dereferencer)
        name = parameter['name']
        if name in seen:
            raise InvalidAppApi('Duplicate parameter {0} in app {1} for action {2}'.format(name, app_name, action_name))
        seen.add(name)


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
    4. Validate that the defaults are valid for the given type (Do not do. Could be useful to have non-conforming defaults)
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