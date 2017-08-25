import unittest
from server.appdevice import App, Device


class TestAppDatabase(unittest.TestCase):

    def setUp(self):
        encrypted_fields = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': True},
                            {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': True}]
        plaintext_fields = [{'name': 'test3', 'type': 'boolean', 'value': True, 'encrypted': False},
                            {'name': 'test4', 'type': 'string', 'value': 'something else', 'encrypted': False}]
        encrypted_fields_as_json = list(encrypted_fields)
        for field in encrypted_fields:
            field.pop('value')
        both_fields = list(encrypted_fields)
        both_fields.extend(plaintext_fields)
        both_fields_as_json = list(encrypted_fields_as_json)
        both_fields_as_json.extend(plaintext_fields)
        self.device1_json = {'name': 'test1', 'fields': encrypted_fields}
        self.device1_as_json = {'name': 'test1', 'fields': encrypted_fields_as_json}
        self.device2_json = {'name': 'test2', 'fields': plaintext_fields}
        self.device3_json = {'name': 'test3', 'fields': both_fields}
        self.device3_as_json = {'name': 'test3', 'fields': both_fields_as_json}

    def assertConstructionIsCorrect(self, app, name, devices):
        self.assertEqual(app.name, name)
        self.assertSetEqual({device.name for device in app.devices}, devices)

    def test_init_name_only(self):
        app = App('test')
        self.assertConstructionIsCorrect(app, 'test', set())

    def test_init_with_devices(self):
        app = App('test', devices_json=[self.device1_json, self.device2_json, self.device3_json])
        self.assertConstructionIsCorrect(app, 'test', {'test1', 'test2', 'test3'})

    def test_get_device(self):
        app = App('test', devices_json=[self.device1_json, self.device2_json, self.device3_json])
        self.assertEqual(app.get_device('test2').as_json(), self.device2_json)

    def test_get_device_invalid(self):
        app = App('test', devices_json=[self.device1_json, self.device2_json, self.device3_json])
        self.assertIsNone(app.get_device('invalid'))

    def test_as_json(self):
        app = App('test', devices_json=[self.device1_json, self.device2_json, self.device3_json])
        self.assertDictEqual(
            app.as_json(), {'name': 'test', 'fields': [self.device1_as_json, self.device2_json, self.device3_as_json]})