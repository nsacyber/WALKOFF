import unittest
from core.config.config import initialize
from core.validator import validate_parameter, validate_parameters
from core.helpers import InvalidInput


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
            with self.assertRaises(InvalidInput):
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
        with self.assertRaises(InvalidInput):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_integer_cause_string(self):
        parameter_api = {'name': 'name1', 'type': 'integer'}
        value = 'abc'
        with self.assertRaises(InvalidInput):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_integer_cause_float_string(self):
        parameter_api = {'name': 'name1', 'type': 'integer'}
        value = '3.27'
        with self.assertRaises(InvalidInput):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_no_formats_invalid_boolean(self):
        parameter_api = {'name': 'name1', 'type': 'boolean'}
        value = 'abc'
        with self.assertRaises(InvalidInput):
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
        with self.assertRaises(InvalidInput):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameter_primitive_string_format_enum_invalid(self):
        parameter_api = {'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']}
        value = 'test2'
        with self.assertRaises(InvalidInput):
            validate_parameter(value, parameter_api, self.message)

    def test_validate_parameters_all_valid_no_defaults(self):
        parameter_apis = [{'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
                          {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
                          {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725}]
        inputs = {'name1': 'test', 'name2': '5', 'name3': '10.2378'}
        expected = {'name1': 'test', 'name2': 5, 'name3': 10.2378}
        self.assertDictEqual(validate_parameters(parameter_apis, inputs, self.message), expected)

    def test_validate_parameters_invalid_no_defaults(self):
        parameter_apis = [{'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
                          {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
                          {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725}]
        inputs = {'name1': 'test', 'name2': '5', 'name3': '-11.2378'}
        with self.assertRaises(InvalidInput):
            validate_parameters(parameter_apis, inputs, self.message)

    def test_validate_parameters_missing_with_valid_default(self):
        parameter_apis = [{'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
                          {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
                          {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725, 'default': 10.25}]
        inputs = {'name1': 'test', 'name2': '5'}
        expected = {'name1': 'test', 'name2': 5, 'name3': 10.25}
        self.assertDictEqual(validate_parameters(parameter_apis, inputs, self.message), expected)

    def test_validate_parameters_missing_with_invalid_default(self):
        parameter_apis = [{'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
                          {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
                          {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725, 'default': 'abc'}]
        inputs = {'name1': 'test', 'name2': '5'}
        expected = {'name1': 'test', 'name2': 5, 'name3': 'abc'}
        self.assertDictEqual(validate_parameters(parameter_apis, inputs, self.message), expected)

    def test_validate_parameters_missing_without_default(self):
        parameter_apis = [{'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
                          {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25},
                          {'name': 'name3', 'type': 'number', 'minimum': -10.5, 'maximum': 30.725}]
        inputs = {'name1': 'test', 'name2': '5'}
        with self.assertRaises(InvalidInput):
            validate_parameters(parameter_apis, inputs, self.message)

    def test_validate_parameters_too_many_inputs(self):
        parameter_apis = [{'name': 'name1', 'type': 'string', 'minLength': 1, 'maxLength': 25, 'enum': ['test', 'test3']},
                          {'name': 'name2', 'type': 'integer', 'minimum': -3, 'maximum': 25}]
        inputs = {'name1': 'test', 'name2': '5', 'name3': '-11.2378'}
        with self.assertRaises(InvalidInput):
            validate_parameters(parameter_apis, inputs, self.message)