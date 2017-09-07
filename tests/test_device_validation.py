import unittest
from core.validator import validate_device, validate_device_fields, InvalidInput


class TestDeviceValidation(unittest.TestCase):
    def test_basic_device_fields_validation(self):
        device_fields = [{'name': 'param1', 'type': 'string'}, {'name': 'param2', 'type': 'boolean'}]
        device_in = {'param1': 'somevalue', 'param2': True}
        validate_device_fields(device_fields, device_in, '')

    def test_basic_device_fields_validation_invalid_type(self):
        device_fields = [{'name': 'param1', 'type': 'string'}, {'name': 'param2', 'type': 'boolean'}]
        device_in = {'param1': 'somevalue', 'param2': 'invalid'}
        with self.assertRaises(InvalidInput):
            validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_no_fields_none_required(self):
        device_fields = [{'name': 'param1', 'type': 'string'}, {'name': 'param2', 'type': 'boolean'}]
        device_in = {}
        validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_encryption_true(self):
        device_fields = [{'name': 'param1', 'type': 'string', 'encrypted': True}, {'name': 'param2', 'type': 'boolean'}]
        device_in = {'param1': 'somevalue', 'param2': True}
        validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_encryption_false(self):
        device_fields = [{'name': 'param1', 'type': 'string', 'encrypted': False},
                         {'name': 'param2', 'type': 'boolean'}]
        device_in = {'param1': 'somevalue', 'param2': True}
        validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_encryption_with_invalid_value(self):
        device_fields = [{'name': 'param1', 'type': 'integer', 'encrypted': True},
                         {'name': 'param2', 'type': 'boolean'}]
        device_in = {'param1': 'somevalue', 'param2': True}
        with self.assertRaises(InvalidInput):
            validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_all_required_in_api(self):
        device_fields = [{'name': 'param1', 'type': 'string', 'required': True},
                         {'name': 'param2', 'type': 'boolean', 'required': True}]
        device_in = {'param1': 'somevalue', 'param2': True}
        validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_some_required_in_api(self):
        device_fields = [{'name': 'param1', 'type': 'string', 'required': True},
                         {'name': 'param2', 'type': 'boolean'}]
        device_in = {'param1': 'somevalue', 'param2': True}
        validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_all_required_in_api_no_fields(self):
        device_fields = [{'name': 'param1', 'type': 'string', 'required': True},
                         {'name': 'param2', 'type': 'boolean', 'required': True}]
        device_in = {}
        with self.assertRaises(InvalidInput):
            validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_some_required_in_api_no_fields(self):
        device_fields = [{'name': 'param1', 'type': 'string', 'required': True},
                         {'name': 'param2', 'type': 'boolean'}]
        device_in = {}
        with self.assertRaises(InvalidInput):
            validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_some_required_in_api_too_few_fields(self):
        device_fields = [{'name': 'param1', 'type': 'string', 'required': True},
                         {'name': 'param2', 'type': 'boolean'}]
        device_in = {'param2': True}
        with self.assertRaises(InvalidInput):
            validate_device_fields(device_fields, device_in, '')

    def test_device_fields_validation_with_required_and_encrypted(self):
        device_fields = [{'name': 'param1', 'type': 'string', 'required': True, 'encrypted': True},
                         {'name': 'param2', 'type': 'boolean'}]
        device_in = {'param1': 'somevalue', 'param2': True}
        validate_device_fields(device_fields, device_in, '')

    def test_validate_device_valid_fields(self):
        device = {'type1': {'description': 'something',
                            'fields': [{'name': 'param1', 'type': 'string', 'required': True, 'encrypted': True},
                                       {'name': 'param2', 'type': 'boolean'}]}}
        device_in = {'type': 'type1', 'app': 'app1', 'fields': {'param1': 'somevalue', 'param2': True}}
        validate_device(device, device_in)

    def test_validate_device_valid_fields_multiple_device_type_apis(self):
        device = {'type1': {'description': 'something',
                            'fields': [{'name': 'param1', 'type': 'string', 'required': True, 'encrypted': True},
                                       {'name': 'param2', 'type': 'boolean'}]},
                  'type2': {'description': 'something_else',
                            'fields': [{'name': 'p1', 'type': 'integer', 'encrypted': True},
                                       {'name': 'p2', 'type': 'boolean', 'required': True}]}}
        device_in = {'type': 'type1', 'app': 'app1', 'fields': {'param1': 'somevalue', 'param2': True}}
        validate_device(device, device_in)

    def test_validate_device_invalid_device_type(self):
        device = {'type1': {'description': 'something',
                            'fields': [{'name': 'param1', 'type': 'string', 'required': True, 'encrypted': True},
                                       {'name': 'param2', 'type': 'boolean'}]},
                  'type2': {'description': 'something_else',
                            'fields': [{'name': 'p1', 'type': 'integer', 'encrypted': True},
                                       {'name': 'p2', 'type': 'boolean', 'required': True}]}}
        device_in = {'type': 'invalid', 'app': 'app1', 'fields': {'param1': 'somevalue', 'param2': True}}
        with self.assertRaises(InvalidInput):
            validate_device(device, device_in)

