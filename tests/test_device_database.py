import unittest

from walkoff.executiondb.device import Device, UnknownDeviceField, DeviceField, EncryptedDeviceField, \
    get_device_ids_by_fields
from tests.util import execution_db_help
from tests.util import initialize_test_config


class TestDeviceDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        cls.execution_db, _ = execution_db_help.setup_dbs()

    def tearDown(self):
        execution_db_help.cleanup_execution_db()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()

    def assertConstructionIsCorrect(self, device, name, plaintext_fields, encrypted_fields, device_type,
                                    description=''):
        self.assertEqual(device.name, name)
        self.assertListEqual([x for x in device.plaintext_fields], plaintext_fields)
        self.assertListEqual([x for x in device.encrypted_fields], encrypted_fields)
        self.assertEqual(device.type, device_type)
        self.assertEqual(device.description, description)

    def test_init_name_only(self):
        device = Device('test', [], [], 'type')
        self.assertConstructionIsCorrect(device, 'test', [], [], 'type')

    def test_init_with_description(self):
        device = Device('test', [], [], 'type', description='desc')
        self.assertConstructionIsCorrect(device, 'test', [], [], 'type', description='desc')

    def test_init_with_plaintext(self):
        fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        device = Device('test', fields, [], 'type')
        self.assertConstructionIsCorrect(device, 'test', fields, [], 'type')

    def test_init_with_encrypted(self):
        fields = [EncryptedDeviceField('test_name', 'integer', 123),
                  EncryptedDeviceField('test2', 'string', 'something')]
        device = Device('test', [], fields, 'type')
        self.assertConstructionIsCorrect(device, 'test', [], fields, 'type')

    def test_init_with_both_plaintext_and_encrypted(self):
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_fields = [EncryptedDeviceField('test3', 'boolean', True),
                            EncryptedDeviceField('test4', 'string', 'something else')]
        device = Device('test', plaintext_fields, encrypted_fields, 'type')
        self.assertConstructionIsCorrect(device, 'test', plaintext_fields, encrypted_fields, 'type')

    def test_get_plaintext_fields_no_fields(self):
        device = Device('test', [], [], 'type')
        self.assertDictEqual(device.get_plaintext_fields(), {})

    def test_get_plaintext_fields_plaintext_only(self):
        fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        device = Device('test', fields, [], 'type')
        self.assertDictEqual(device.get_plaintext_fields(), {'test_name': 123, 'test2': 'something'})

    def test_get_plaintext_fields_with_encrypted(self):
        encrypted_fields = [EncryptedDeviceField('test_name', 'integer', 123),
                            EncryptedDeviceField('test2', 'string', 'something')]
        plaintext_fields = [DeviceField('test3', 'boolean', True), DeviceField('test4', 'string', 'something else')]
        device = Device('test', plaintext_fields, encrypted_fields, 'type')
        self.assertDictEqual(device.get_plaintext_fields(), {'test3': True, 'test4': 'something else'})

    def test_get_encrypted_field(self):
        fields = [EncryptedDeviceField('test_name', 'integer', 123),
                  EncryptedDeviceField('test2', 'string', 'something')]
        device = Device('test', [], fields, 'type')
        self.assertEqual(device.get_encrypted_field('test_name'), 123)

    def test_get_encrypted_field_dne(self):
        fields = [EncryptedDeviceField('test_name', 'integer', 123),
                  EncryptedDeviceField('test2', 'string', 'something')]
        device = Device('test', [], fields, 'type')
        with self.assertRaises(UnknownDeviceField):
            device.get_encrypted_field('invalid')

    def test_as_json(self):
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_fields = [EncryptedDeviceField('test3', 'boolean', True),
                            EncryptedDeviceField('test4', 'string', 'something else')]
        device = Device('test', plaintext_fields, encrypted_fields, 'type', description='desc')
        device_json = device.as_json()
        self.assertEqual(device_json['name'], 'test')
        self.assertEqual(device_json['type'], 'type')
        self.assertEqual(device_json['description'], 'desc')
        plaintext_fields.extend(encrypted_fields)
        for field in plaintext_fields:
            self.assertIn(field.as_json(), device_json['fields'])

    def test_from_json(self):
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_field1 = EncryptedDeviceField('test3', 'boolean', True)
        encrypted_field2 = EncryptedDeviceField('test4', 'string', 'something else')
        encrypted_fields = [encrypted_field1, encrypted_field2]

        encrypted_field_json1 = encrypted_field1.as_json()
        encrypted_field_json2 = encrypted_field2.as_json()
        encrypted_field_json1_with_value = dict(encrypted_field_json1)
        encrypted_field_json2_with_value = dict(encrypted_field_json2)
        encrypted_field_json1_with_value['value'] = True
        encrypted_field_json2_with_value['value'] = 'something_else'

        fields_json = [field.as_json() for field in plaintext_fields]
        fields_json.extend([encrypted_field_json1_with_value, encrypted_field_json2_with_value])

        device = Device.from_json({'name': 'test', 'fields': fields_json, 'type': 'something', 'description': 'desc'})

        expected_plaintext_fields_as_json = [field.as_json() for field in plaintext_fields]
        expected_encrypted_fields_as_json = [field.as_json() for field in encrypted_fields]

        self.assertEqual(device.name, 'test')
        self.assertEqual(device.type, 'something')
        self.assertEqual(device.description, 'desc')
        for field in device.plaintext_fields:
            self.assertIn(field.as_json(), expected_plaintext_fields_as_json)
        for field in device.encrypted_fields:
            self.assertIn(field.as_json(), expected_encrypted_fields_as_json)

    def test_construct_fields_from_json(self):
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_field1 = EncryptedDeviceField('test3', 'boolean', True)
        encrypted_field2 = EncryptedDeviceField('test4', 'string', 'something else')

        encrypted_field_json1 = encrypted_field1.as_json()
        encrypted_field_json2 = encrypted_field2.as_json()
        encrypted_field_json1['value'] = True
        encrypted_field_json2['value'] = 'something_else'
        fields_json = [field.as_json() for field in plaintext_fields]
        fields_json.extend([encrypted_field_json1, encrypted_field_json2])

        plaintext_fields, encrypted_fields = Device._construct_fields_from_json(fields_json)
        self.assertSetEqual({field.name for field in plaintext_fields}, {'test_name', 'test2'})
        self.assertSetEqual({field.name for field in encrypted_fields}, {'test3', 'test4'})

    def test_update_from_json_name_only(self):
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_fields = [EncryptedDeviceField('test3', 'boolean', True),
                            EncryptedDeviceField('test4', 'string', 'something else')]
        device = Device('test', plaintext_fields, encrypted_fields, 'type', description='desc')
        device.update_from_json({'name': 'new_name'}, True)
        self.assertConstructionIsCorrect(device, 'new_name', plaintext_fields, encrypted_fields, 'type',
                                         description='desc')

    def test_update_from_json_description_only(self):
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_fields = [EncryptedDeviceField('test3', 'boolean', True),
                            EncryptedDeviceField('test4', 'string', 'something else')]
        device = Device('test', plaintext_fields, encrypted_fields, 'type', description='desc')
        device.update_from_json({'description': 'new_desc'}, True)
        self.assertConstructionIsCorrect(device, 'test', plaintext_fields, encrypted_fields, 'type',
                                         description='new_desc')

    def test_update_from_json_type_only(self):
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_fields = [EncryptedDeviceField('test3', 'boolean', True),
                            EncryptedDeviceField('test4', 'string', 'something else')]
        device = Device('test', plaintext_fields, encrypted_fields, 'type', description='desc')
        device.update_from_json({'type': 'new_type'}, True)
        self.assertConstructionIsCorrect(device, 'test', plaintext_fields, encrypted_fields, 'new_type',
                                         description='desc')

    def test_update_from_json_with_plaintext_fields(self):
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_fields = [EncryptedDeviceField('test3', 'boolean', True),
                            EncryptedDeviceField('test4', 'string', 'something else')]
        new_plaintext_fields = [DeviceField('new_test_name', 'integer', 451),
                                DeviceField('new_test2', 'string', 'changed')]
        device = Device('test', plaintext_fields, encrypted_fields, 'type', description='desc')
        device.update_from_json({'fields': [field.as_json() for field in new_plaintext_fields]}, True)
        self.assertEqual(device.name, 'test')
        self.assertEqual(device.type, 'type')
        self.assertEqual(device.description, 'desc')
        self.assertSetEqual({field.name for field in device.plaintext_fields}, {'new_test_name', 'new_test2'})
        self.assertSetEqual({field.name for field in device.encrypted_fields}, set())

    def test_update_from_json_with_encrypted_fields(self):
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_fields = [EncryptedDeviceField('test3', 'boolean', True),
                            EncryptedDeviceField('test4', 'string', 'something else')]
        new_encrypted_fields = [EncryptedDeviceField('new_test3', 'boolean', True),
                                EncryptedDeviceField('new_test4', 'string', 'something else')]
        encrypted_field_json1 = new_encrypted_fields[0].as_json()
        encrypted_field_json2 = new_encrypted_fields[1].as_json()
        encrypted_field_json1['value'] = True
        encrypted_field_json2['value'] = 'something_else'
        device = Device('test', plaintext_fields, encrypted_fields, 'type', description='desc')
        device.update_from_json({'fields': [encrypted_field_json1, encrypted_field_json2]}, True)
        self.assertEqual(device.name, 'test')
        self.assertEqual(device.type, 'type')
        self.assertEqual(device.description, 'desc')
        self.assertSetEqual({field.name for field in device.plaintext_fields}, set())
        self.assertSetEqual({field.name for field in device.encrypted_fields}, {'new_test3', 'new_test4'})

    def test_get_device_ids(self):
        device_one = Device('test',
                            [DeviceField('valid_one', 'integer', 123), DeviceField('valid_two', 'string', '456'),
                             DeviceField('invalid', 'integer', 789)], [], 'type', description='desc')

        device_two = Device('test',
                            [DeviceField('valid_one', 'integer', 123), DeviceField('valid_two', 'string', '456')], [],
                            'type', description='desc')

        device_three = Device('test',
                              [DeviceField('valid_one', 'string', '456'), DeviceField('valid_two', 'integer', 123)], [],
                              'type', description='desc')

        device_four = Device('test',
                             [DeviceField('valid_one', 'integer', 123), DeviceField('invalid', 'integer', 789)], [],
                             'type', description='desc')

        self.execution_db.session.add_all([device_one, device_two, device_three, device_four])
        self.execution_db.session.commit()

        device_ids = get_device_ids_by_fields({'valid_one': 123, 'valid_two': '456'})
        self.assertEqual(len(device_ids), 2)
        self.assertIn(device_one.id, device_ids)
        self.assertIn(device_two.id, device_ids)
