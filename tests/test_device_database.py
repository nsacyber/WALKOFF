import unittest
from server.appdevice import Device, UnknownDeviceField


class TestDeviceDatabase(unittest.TestCase):

    def assertConstructionIsCorrect(self, device, name, plaintext_fields, encrypted_fields):
        self.assertEqual(device.name, name)
        self.assertListEqual([field.as_json() for field in device.plaintext_fields], plaintext_fields)
        self.assertListEqual([field.as_json() for field in device.encrypted_fields], encrypted_fields)

    def test_init_name_only(self):
        device = Device('test', [])
        self.assertConstructionIsCorrect(device, 'test', [], [])

    def test_init_with_plaintext(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': False}]
        device = Device('test', fields_json)
        self.assertConstructionIsCorrect(device, 'test', fields_json, [])

    def test_init_with_encrypted(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': True},
                       {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': True}]
        device = Device('test', fields_json)
        for field in fields_json:
            field.pop('value')
        self.assertConstructionIsCorrect(device, 'test', [], fields_json)

    def test_init_with_both_plaintext_and_encrypted(self):
        encrypted_fields = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': True},
                        {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': True}]
        plaintext_fields = [{'name': 'test3', 'type': 'boolean', 'value': True, 'encrypted': False},
                            {'name': 'test4', 'type': 'string', 'value': 'something else', 'encrypted': False}]
        both_fields = list(encrypted_fields)
        both_fields.extend(plaintext_fields)
        device = Device('test', both_fields)
        for field in encrypted_fields:
            field.pop('value')
        self.assertConstructionIsCorrect(device, 'test', plaintext_fields, encrypted_fields)

    def test_get_plaintext_fields_no_fields(self):
        device = Device('test', [])
        self.assertDictEqual(device.get_plaintext_fields(), {})

    def test_get_plaintext_fields_plaintext_only(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': False}]
        device = Device('test', fields_json)
        self.assertDictEqual(device.get_plaintext_fields(), {'test_name': 123, 'test2': 'something'})

    def test_get_plaintext_fields_with_encrypted(self):
        encrypted_fields = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': True},
                            {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': True}]
        plaintext_fields = [{'name': 'test3', 'type': 'boolean', 'value': True, 'encrypted': False},
                            {'name': 'test4', 'type': 'string', 'value': 'something else', 'encrypted': False}]
        both_fields = list(encrypted_fields)
        both_fields.extend(plaintext_fields)
        device = Device('test', both_fields)
        self.assertDictEqual(device.get_plaintext_fields(), {'test3': True, 'test4': 'something else'})

    def test_get_encrypted_field(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': True},
                       {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': True}]
        device = Device('test', fields_json)
        self.assertEqual(device.get_encrypted_field('test_name'), 123)

    def test_get_encrypted_field_dne(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': True},
                       {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': True}]
        device = Device('test', fields_json)
        with self.assertRaises(UnknownDeviceField):
            device.get_encrypted_field('invalid')

    def test_as_json(self):
        encrypted_fields = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': True},
                            {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': True}]
        plaintext_fields = [{'name': 'test3', 'type': 'boolean', 'value': True, 'encrypted': False},
                            {'name': 'test4', 'type': 'string', 'value': 'something else', 'encrypted': False}]
        both_fields = list(encrypted_fields)
        both_fields.extend(plaintext_fields)
        device = Device('test', both_fields)
        for field in (field for field in both_fields if field['encrypted']):
            field.pop('value')
        self.maxDiff = None
        device_json = device.as_json()
        for field in device_json['fields']:
            self.assertIn(field, both_fields)
        self.assertEqual(device_json['name'], 'test')

    def test_from_json(self):
        encrypted_fields = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': True},
                            {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': True}]
        plaintext_fields = [{'name': 'test3', 'type': 'boolean', 'value': True, 'encrypted': False},
                            {'name': 'test4', 'type': 'string', 'value': 'something else', 'encrypted': False}]
        both_fields = list(encrypted_fields)
        both_fields.extend(plaintext_fields)
        device = Device.from_json({'name': 'test', 'fields': both_fields})
        for field in encrypted_fields:
            field.pop('value')
        self.assertConstructionIsCorrect(device, 'test', plaintext_fields, encrypted_fields)
