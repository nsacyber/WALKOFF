import unittest
import json

from walkoff.appgateway.validator import validate_parameter, validate_parameters, convert_json
from walkoff.config import initialize
from walkoff.executiondb.argument import Argument
from walkoff.helpers import InvalidArgument


class TestInputValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize()
        cls.message = 'app1 action1'

    def test_validate_parameter_primitive_no_formats_not_required_valid_string(self):
        parameter_api = {'name': 'name1', 'type': 'string'}
        value = 'test string'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), value)
        value = ''
        self.assertEqual(validate_parameter(value, parameter_api, self.message), value)

    def test_validate_parameter_primitive_no_formats_not_required_valid_number(self):
        parameter_api = {'name': 'name1', 'type': 'number'}
        value = '3.27'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), 3.27)

    def test_validate_parameter_primitive_no_formats_not_required_valid_negative_number(self):
        parameter_api = {'name': 'name1', 'type': 'number'}
        value = '-3.27'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), -3.27)

    def test_validate_parameter_primitive_no_formats_not_required_valid_int(self):
        parameter_api = {'name': 'name1', 'type': 'integer'}
        value = '3'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), 3)

    def test_validate_parameter_primitive_no_formats_not_required_valid_int_from_float(self):
        parameter_api = {'name': 'name1', 'type': 'integer'}
        value = 3.27
        self.assertEqual(validate_parameter(value, parameter_api, self.message), 3)

    def test_validate_parameter_primitive_no_formats_not_required_valid_negative_int(self):
        parameter_api = {'name': 'name1', 'type': 'integer'}
        value = '-3'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), -3)

    def test_validate_parameter_primitive_user(self):
        parameter_api = {'name': 'name1', 'type': 'user'}
        value = '3'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), 3)

    def test_validate_parameter_primitive_role(self):
        parameter_api = {'name': 'name1', 'type': 'role'}
        value = '42'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), 42)

    def test_validate_parameter_primitive_no_formats_not_required_valid_bool(self):
        parameter_api = {'name': 'name1', 'type': 'boolean'}
        true_values = ['true', 'True', 'TRUE', 'TrUe']
        false_values = ['false', 'False', 'FALSE', 'FaLSe']
        for true_value in true_values:
            self.assertEqual(validate_parameter(true_value, parameter_api, self.message), True)
        for false_value in false_values:
            self.assertEqual(validate_parameter(false_value, parameter_api, self.message), False)

    def test_validate_parameter_primitive_no_formats_required_string(self):
        parameter_api = {'name': 'name1', 'type': 'string', 'required': True}
        value = 'test string'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), value)
        value = ''
        self.assertEqual(validate_parameter(value, parameter_api, self.message), value)

    def test_validate_parameter_primitive_no_formats_required_none(self):
        parameter_apis = [{'name': 'name1', 'type': 'string', 'required': True},
                          {'name': 'name1', 'type': 'number', 'required': True},
                          {'name': 'name1', 'type': 'integer', 'required': True},
                          {'name': 'name1', 'type': 'boolean', 'required': True}]
        for parameter_api in parameter_apis:
            with self.assertRaises(InvalidArgument):
                validate_parameter(None, parameter_api, self.message)

    def test_validate_parameter_primitive_not_required_none(self):
        parameter_apis = [{'name': 'name1', 'type': 'string', 'required': False},
                          {'name': 'name1', 'type': 'number', 'required': False},
                          {'name': 'name1', 'type': 'integer'},
                          {'name': 'name1', 'type': 'boolean'}]
        for parameter_api in parameter_apis:
            self.assertIsNone(validate_parameter(None, parameter_api, self.message))

    def test_validate_parameter_primitive_no_formats_invalid_number(self):
        parameter_api = {'name': 'name1', 'type': 'number'}
        value = 'abc'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_integer_cause_string(self):
        parameter_api = {'name': 'name1', 'type': 'integer'}
        value = 'abc'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_user_cause_string(self):
        parameter_api = {'name': 'name1', 'type': 'user'}
        value = 'abc'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_role_cause_string(self):
        parameter_api = {'name': 'name1', 'type': 'role'}
        value = 'admin'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_user_cause_0(self):
        parameter_api = {'name': 'name1', 'type': 'user'}
        value = '0'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_role_cause_0(self):
        parameter_api = {'name': 'name1', 'type': 'role'}
        value = '0'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_integer_cause_float_string(self):
        parameter_api = {'name': 'name1', 'type': 'integer'}
        value = '3.27'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_boolean(self):
        parameter_api = {'name': 'name1', 'type': 'boolean'}
        value = 'abc'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_string_format_valid(self):
        parameter_api = {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25}
        value = 'test string'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), value)

    def test_validate_parameter_primitive_string_format_enum_valid(self):
        parameter_api = {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']}
        value = 'test'
        self.assertEqual(validate_parameter(value, parameter_api, self.message), value)

    def test_validate_parameter_primitive_string_format_invalid(self):
        parameter_api = {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 3}
        value = 'test string'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_string_format_enum_invalid(self):
        parameter_api = {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']}
        value = 'test2'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_object(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'object',
                       'required': ['a', 'b'],
                       'properties':
                           {'a': {'type': 'number'},
                            'b': {'type': 'string'},
                            'c': {'type': 'boolean'}}}}
        value = {'a': 435.6, 'b': 'aaaa', 'c': True}
        validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_object_from_string(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'object',
                       'required': ['a', 'b'],
                       'properties':
                           {'a': {'type': 'number'},
                            'b': {'type': 'string'},
                            'c': {'type': 'boolean'}}}}
        value = json.dumps({'a': 435.6, 'b': 'aaaa', 'c': True})
        validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_object_invalid(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'object',
                       'required': ['a', 'b'],
                       'properties':
                           {'a': {'type': 'number'},
                            'b': {'type': 'string'},
                            'c': {'type': 'boolean'}}}}
        value = {'a': 435.6, 'invalid': 'aaaa', 'c': True}
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_object_array(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'array',
                       'items': {'type': 'object',
                                 'properties': {'A': {'type': 'string'},
                                                'B': {'type': 'integer'}}}
                       }}
        value = [{'A': 'string in', 'B': '33'}, {'A': 'string2', 'B': '7'}]
        validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_object_array_invalid(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'array',
                       'items': {'type': 'object',
                                 'properties': {'A': {'type': 'string'},

                                                'B': {'type': 'integer'}}}
                       }}
        value = [{'A': 'string in', 'B': '33'}, {'A': 'string2', 'B': 'invalid'}]
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_invalid_data_type(self):
        parameter_api = {'name': 'name1', 'type': 'invalid', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']}
        value = 'test2'
        with self.assertRaises(InvalidArgument):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameters_all_valid_no_defaults(self):
        parameter_apis = [
            {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
            {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
            {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725}]
        arguments = [Argument('name1', value='test'),
                     Argument('name2', value='5'),
                     Argument('name3', value='10.2378')]
        expected = {'name1': 'test', 'name2': 5, 'name3': 10.2378}
        self.assertDictEqual(validate_parameters(parameter_apis, arguments, self.message), expected)

    def test_validate_parameters_invalid_no_defaults(self):
        parameter_apis = [
            {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
            {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
            {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725}]
        arguments = [Argument('name1', value='test'),
                     Argument('name2', value='5'),
                     Argument('name3', value='-11.2378')]
        with self.assertRaises(InvalidArgument):
            validate_parameters(parameter_apis, arguments, self.message)

    def test_validate_parameters_missing_with_valid_default(self):
        parameter_apis = [
            {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
            {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
            {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725, 'default': 10.25}]
        arguments = [Argument('name1', value='test'),
                     Argument('name2', value='5')]
        expected = {'name1': 'test', 'name2': 5, 'name3': 10.25}
        self.assertDictEqual(validate_parameters(parameter_apis, arguments, self.message), expected)

    def test_validate_parameters_missing_with_invalid_default(self):
        parameter_apis = [
            {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
            {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
            {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725, 'default': 'abc'}]
        arguments = [Argument('name1', value='test'),
                     Argument('name2', value='5')]
        expected = {'name1': 'test', 'name2': 5, 'name3': 'abc'}
        self.assertDictEqual(validate_parameters(parameter_apis, arguments, self.message), expected)

    def test_validate_parameters_missing_without_default(self):
        parameter_apis = [
            {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
            {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
            {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725}]
        arguments = [Argument('name1', value='test'),
                     Argument('name2', value='5')]
        expected = {'name1': 'test', 'name2': 5, 'name3': None}
        self.assertAlmostEqual(validate_parameters(parameter_apis, arguments, self.message), expected)

    def test_validate_parameters_missing_required_without_default(self):
        parameter_apis = [
            {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
            {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
            {'name': 'name3', 'type': 'number', 'required': True, 'minimum': -10.5, 'maximum': 30.725}]
        arguments = [Argument('name1', value='test'),
                     Argument('name2', value='5')]
        with self.assertRaises(InvalidArgument):
            validate_parameters(parameter_apis, arguments, self.message)

    def test_validate_parameters_too_many_inputs(self):
        parameter_apis = [
            {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
            {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25}]
        arguments = [Argument('name1', value='test'),
                     Argument('name2', value='5'),
                     Argument('name3', value='-11.2378')]
        with self.assertRaises(InvalidArgument):
            validate_parameters(parameter_apis, arguments, self.message)

    def test_validate_parameters_skip_action_references(self):
        parameter_apis = [
            {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
            {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
            {'name': 'name3', 'type': 'number', 'required': True, 'minimum': -10.5, 'maximum': 30.725}]
        arguments = [Argument('name1', value='test'),
                     Argument('name2', value='5'),
                     Argument('name3', reference='action1')]
        expected = {'name1': 'test', 'name2': 5}
        self.assertDictEqual(validate_parameters(parameter_apis, arguments, self.message), expected)

    def test_validate_parameters_skip_action_references_inputs_non_string(self):
        parameter_apis = [
            {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
            {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
            {'name': 'name3', 'type': 'number', 'required': True, 'minimum': -10.5, 'maximum': 30.725}]
        arguments = [Argument('name1', value='test'),
                     Argument('name2', value=5),
                     Argument('name3', reference='action1')]
        expected = {'name1': 'test', 'name2': 5}
        self.assertDictEqual(validate_parameters(parameter_apis, arguments, self.message), expected)

    def test_convert_json(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'object',
                       'required': ['a', 'b'],
                       'properties':
                           {'a': {'type': 'number'},
                            'b': {'type': 'string'},
                            'c': {'type': 'boolean'}}}}
        value = {'a': '435.6', 'b': 'aaaa', 'c': 'true'}
        converted = convert_json(parameter_api, value, self.message)
        self.assertDictEqual(converted, {'a': 435.6, 'b': 'aaaa', 'c': True})

    def test_convert_json_invalid(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'object',
                       'required': ['a', 'b'],
                       'properties':
                           {'a': {'type': 'number'},
                            'b': {'type': 'string'},
                            'c': {'type': 'boolean'}}}}
        value = {'a': '435.6', 'b': 'aaaa', 'c': 'invalid'}
        with self.assertRaises(InvalidArgument):
            convert_json(parameter_api, value, self.message)

    def test_convert_json_nested(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'object',
                       'required': ['a', 'b'],
                       'properties':
                           {'a': {'type': 'number'},
                            'b': {'type': 'string'},
                            'c': {'type': 'object',
                                  'properties': {'A': {'type': 'string'},
                                                 'B': {'type': 'integer'}}}}}}
        value = {'a': '435.6', 'b': 'aaaa', 'c': {'A': 'string in', 'B': '3'}}
        converted = convert_json(parameter_api, value, self.message)
        self.assertDictEqual(converted, {'a': 435.6, 'b': 'aaaa', 'c': {'A': 'string in', 'B': 3}})

    def test_convert_json_nested_invalid(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'object',
                       'required': ['a', 'b'],
                       'properties':
                           {'a': {'type': 'number'},
                            'b': {'type': 'string'},
                            'c': {'type': 'object',
                                  'properties': {'A': {'type': 'string'},
                                                 'B': {'type': 'integer'}}}}}}
        value = {'a': '435.6', 'b': 'aaaa', 'c': {'A': 'string in', 'B': 'invalid'}}
        with self.assertRaises(InvalidArgument):
            convert_json(parameter_api, value, self.message)

    def test_convert_primitive_array(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'array',
                       'items': {'type': 'number'}}}
        value = ['1.3', '3.4', '555.1', '-132.2']
        converted = convert_json(parameter_api, value, self.message)
        self.assertListEqual(converted, [1.3, 3.4, 555.1, -132.2])

    def test_convert_primitive_array_invalid(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'array',
                       'items': {'type': 'number'}}}
        value = ['1.3', '3.4', '555.1', 'invalid']
        with self.assertRaises(InvalidArgument):
            convert_json(parameter_api, value, self.message)

    def test_convert_object_array(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'array',
                       'items': {
                           'type': 'object',
                           'properties': {'A': {'type': 'string'},
                                          'B': {'type': 'integer'}}}
                       }}
        value = [{'A': 'string in', 'B': '33'}, {'A': 'string2', 'B': '7'}]
        expected = [{'A': 'string in', 'B': 33}, {'A': 'string2', 'B': 7}]
        converted = convert_json(parameter_api, value, self.message)
        self.assertEqual(len(converted), len(expected))
        for i in range(len(converted)):
            self.assertDictEqual(converted[i], expected[i])

    def test_convert_object_array_invalid(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'array',
                       'items': {
                           'type': 'object',
                           'properties': {'A': {'type': 'string'},
                                          'B': {'type': 'integer'}}}
                       }}
        value = [{'A': 'string in', 'B': '33'}, {'A': 'string2', 'B': 'invalid'}]
        with self.assertRaises(InvalidArgument):
            convert_json(parameter_api, value, self.message)

    def test_convert_object_array_unspecified_type(self):
        parameter_api = {
            'name': 'name1',
            'schema': {'type': 'array'}}
        value = ['@action1', 2, {'a': 'v', 'b': 6}]
        expected = ['@action1', 2, {'a': 'v', 'b': 6}]
        converted = convert_json(parameter_api, value, self.message)
        self.assertListEqual(converted, expected)
