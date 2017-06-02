import unittest
from core.validator import *
import yaml
from tests.config import basic_app_api
from jsonschema.exceptions import RefResolutionError, ValidationError


class TestAppApiValidation(unittest.TestCase):
    """
    This test does not validate if the schema is correct, only the functions associated with further validation
    """
    def setUp(self):
        with open(basic_app_api, 'r') as f:
            self.basicapi = yaml.load(f.read())

    def __generate_resolver_dereferencer(self, spec, expected_success=True):
        try:
            walkoff_resolver = validate_spec_json(
                spec,
                os.path.join('core', 'schemas', 'new_schema.json'),
                '',
                None)
        except Exception as e:
            if expected_success:
                self.fail('Unexpectedly invalid app api. Error: {}'.format(e))
            else:
                raise
        self.dereferencer = partial(deref, resolver=walkoff_resolver)

    def test_dereference_correct_reference_in_same_file(self):
        self.basicapi['definitions'] = {'test_def': {'type': 'object'}}
        self.basicapi['actions']['helloWorld']['returns']['Success']['schema'] = {'$ref': '#/definitions/test_def'}
        self.__generate_resolver_dereferencer(self.basicapi)

    def test_dereference_incorrect_reference_in_same_file(self):
        self.basicapi['definitions'] = {'test_def': {'type': 'object'}}
        self.basicapi['actions']['helloWorld']['returns']['Success']['schema'] = {'$ref': '#/definitions/invalid'}
        with self.assertRaises(RefResolutionError):
            self.__generate_resolver_dereferencer(self.basicapi, expected_success=False)

    def test_validate_definition_empty_required_empty_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object', 'required': [], 'properties': {}}
        with self.assertRaises(ValidationError):
            self.__generate_resolver_dereferencer(self.basicapi, expected_success=False)

    def test_validate_definition_no_required_empty_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object', 'properties': {}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_no_required_no_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object', 'properties': {}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_no_required_with_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_required_all_in_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop1', 'prop2'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_some_required_not_in_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop4', 'prop5'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidAppApi):
            validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_required_matches_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop1', 'prop2', 'prop3'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definitions_all_valid(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop1', 'prop2', 'prop3'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.basicapi['definitions']['def2'] = {'type': 'object',
                                                'required': ['prop1', 'prop2'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.basicapi['definitions']['def3'] = {'type': 'object',
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'}}}
        self.basicapi['definitions']['def4'] = {'type': 'object', 'properties': {}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definitions(self.basicapi['definitions'], self.dereferencer)

    def test_validate_definitions_one_invalid(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop1', 'prop2', 'prop3'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.basicapi['definitions']['def2'] = {'type': 'object',
                                                'required': ['prop4', 'prop5'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidAppApi):
            validate_definitions(self.basicapi['definitions'], self.dereferencer)
