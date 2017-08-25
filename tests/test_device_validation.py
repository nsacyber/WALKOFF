import unittest
from core.validator import validate_device

class TestDeviceValidation(unittest.TestCase):

    def test_basic_device_validation(self):
        device_api = {'dev1': {'description': 'something',
                           'fields': [{'name': 'param1', 'type': 'string', 'required': True},
                                      {'name': 'param2', 'type': 'boolean'}]}}
        device_in = {'somename',
                      'fields': [{'name': 'param1', 'value': 'somevalue'}]}]