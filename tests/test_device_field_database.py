import unittest

from apps.devicedb import EncryptedDeviceField, DeviceField


class TestDeviceField(unittest.TestCase):
    def assertConstructionIsCorrect(self, field, name, field_type, value):
        self.assertEqual(field.name, name)
        self.assertEqual(field.type, field_type)
        self.assertEqual(field.value, value)

    def test_init_basic(self):
        field = DeviceField('test_name', 'string', 'abcd')
        self.assertConstructionIsCorrect(field, 'test_name', 'string', 'abcd')

    def test_init_with_nonstring_value(self):
        field = DeviceField('test_name', 'boolean', True)
        self.assertConstructionIsCorrect(field, 'test_name', 'boolean', True)

    def test_init_with_invalid_type(self):
        field = DeviceField('test_name', 'invalid', 'true')
        self.assertConstructionIsCorrect(field, 'test_name', 'string', 'true')

    def test_init_basic_encrypted(self):
        field = EncryptedDeviceField('test_name', 'string', 'abcd')
        self.assertConstructionIsCorrect(field, 'test_name', 'string', 'abcd')

    def test_init_with_nonstring_value_encrypted(self):
        field = EncryptedDeviceField('test_name', 'boolean', True)
        self.assertConstructionIsCorrect(field, 'test_name', 'boolean', True)

    def test_init_with_invalid_type_encrypted(self):
        field = EncryptedDeviceField('test_name', 'invalid', 'true')
        self.assertConstructionIsCorrect(field, 'test_name', 'string', 'true')

    def test_as_json_basic(self):
        field = DeviceField('test_name', 'integer', 123)
        self.assertDictEqual(field.as_json(),
                             {'name': 'test_name', 'value': 123, 'type': 'integer', 'encrypted': False})

    def test_as_json_basic_encrypted(self):
        field = EncryptedDeviceField('test_name', 'integer', 123)
        self.assertDictEqual(field.as_json(), {'name': 'test_name', 'type': 'integer', 'encrypted': True})

    def test_get_value_encrypted(self):
        field = EncryptedDeviceField('test_name', 'integer', 123)
        self.assertEqual(field.value, 123)

    def test_from_json_basic(self):
        field = DeviceField.from_json({'name': 'test_name', 'type': 'string', 'value': 'abcd'})
        self.assertConstructionIsCorrect(field, 'test_name', 'string', 'abcd')

    def test_from_json_with_nonstring_value(self):
        field = DeviceField.from_json({'name': 'test_name', 'type': 'boolean', 'value': True})
        self.assertConstructionIsCorrect(field, 'test_name', 'boolean', True)

    def test_from_json_with_invalid_type(self):
        field = DeviceField.from_json({'name': 'test_name', 'type': 'invalid', 'value': 'true'})
        self.assertConstructionIsCorrect(field, 'test_name', 'string', 'true')

    def test_from_json_encrypted(self):
        field = EncryptedDeviceField.from_json({'name': 'test_name', 'type': 'string', 'value': 'abcd'})
        self.assertConstructionIsCorrect(field, 'test_name', 'string', 'abcd')

    def test_from_json_with_nonstring_value_encrypted(self):
        field = EncryptedDeviceField.from_json({'name': 'test_name', 'type': 'boolean', 'value': True})
        self.assertConstructionIsCorrect(field, 'test_name', 'boolean', True)

    def test_from_json_with_invalid_type_encrypted(self):
        field = EncryptedDeviceField.from_json({'name': 'test_name', 'type': 'invalid', 'value': 'true'})
        self.assertConstructionIsCorrect(field, 'test_name', 'string', 'true')
