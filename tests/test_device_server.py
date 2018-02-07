import json
import os

import walkoff.config.config
import walkoff.config.paths
import tests.config
from walkoff.coredb.devicedb import Device, App, DeviceField
from walkoff.server.returncodes import *
from tests.util.servertestcase import ServerTestCase
import walkoff.coredb.devicedb


class TestDevicesServer(ServerTestCase):
    def setUp(self):
        self.test_app_name = 'TestApp'

    def tearDown(self):
        walkoff.coredb.devicedb.device_db.session.rollback()
        for device in walkoff.coredb.devicedb.device_db.session.query(Device).all():
            walkoff.coredb.devicedb.device_db.session.delete(device)
        for field in walkoff.coredb.devicedb.device_db.session.query(DeviceField).all():
            walkoff.coredb.devicedb.device_db.session.delete(field)
        app = walkoff.coredb.devicedb.device_db.session.query(App).filter(App.name == self.test_app_name).first()
        if app is not None:
            walkoff.coredb.devicedb.device_db.session.delete(app)
        walkoff.coredb.devicedb.device_db.session.commit()
        walkoff.config.config.app_apis = {}

    def test_read_all_devices_no_devices_in_db(self):
        response = self.get_with_status_check('/api/devices', headers=self.headers, status_code=SUCCESS)
        self.assertListEqual(response, [])

    def test_read_all_devices(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        walkoff.coredb.devicedb.device_db.session.add(app)
        walkoff.coredb.devicedb.device_db.session.commit()
        response = self.get_with_status_check('/api/devices', headers=self.headers, status_code=SUCCESS)
        expected_device1 = device1.as_json()
        expected_device1['app_name'] = 'TestApp'
        expected_device2 = device2.as_json()
        expected_device2['app_name'] = 'TestApp'
        self.assertIn(expected_device1, response)
        self.assertIn(expected_device2, response)

    def test_read_device(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        walkoff.coredb.devicedb.device_db.session.add(device2)
        walkoff.coredb.devicedb.device_db.session.add(device1)
        walkoff.coredb.devicedb.device_db.session.commit()
        response = self.get_with_status_check('/api/devices/{}'.format(device1.id), headers=self.headers,
                                              status_code=SUCCESS)
        expected_device1 = device1.as_json()
        expected_device1['app_name'] = ''
        self.assertEqual(response, expected_device1)

    def test_read_device_does_not_exist(self):
        self.get_with_status_check('/api/devices/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_delete_device(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        walkoff.coredb.devicedb.device_db.session.add(device2)
        walkoff.coredb.devicedb.device_db.session.add(device1)
        walkoff.coredb.devicedb.device_db.session.commit()
        device1_id = device1.id
        self.delete_with_status_check('/api/devices/{}'.format(device1_id), headers=self.headers, status_code=NO_CONTENT)
        self.assertIsNone(walkoff.coredb.devicedb.device_db.session.query(Device).filter(Device.id == device1_id).first())

    def test_delete_device_device_dne(self):
        self.delete_with_status_check('/api/devices/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_create_device_device_already_exists(self):
        device1 = Device('test', [], [], 'type', description='description')
        walkoff.coredb.devicedb.device_db.session.add(device1)
        walkoff.coredb.devicedb.device_db.session.commit()
        device_json = {'app_name': 'test', 'name': 'test', 'type': 'some_type', 'fields': []}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=OBJECT_EXISTS_ERROR, content_type='application/json')

    def test_create_device_app_not_in_apis(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app_name': 'Invalid', 'name': 'test', 'type': 'some_type', 'fields': []}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device_device_type_does_not_exist(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app_name': 'TestApp', 'name': 'test', 'type': 'invalid', 'fields': []}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device_invalid_fields(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app_name': 'TestApp', 'name': 'test', 'type': 'test_type',
                       'fields': [{'name': 'test_name', 'value': 'invalid'}, {'name': 'test2', 'value': 'something'}]}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device_app_not_in_db(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app_name': 'TestApp', 'name': 'test', 'type': 'test_type',
                       'fields': [{'name': 'test_name', 'value': 123}, {'name': 'test2', 'value': 'something'}]}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}
        app = App(name=self.test_app_name)
        walkoff.coredb.devicedb.device_db.session.add(app)
        walkoff.coredb.devicedb.device_db.session.commit()

        device_json = {'app_name': 'TestApp', 'name': 'test', 'type': 'test_type',
                       'fields': [{'name': 'test_name', 'value': 123}, {'name': 'test2', 'value': 'something'}]}
        response = self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                              status_code=OBJECT_CREATED, content_type='application/json')
        device = walkoff.coredb.devicedb.device_db.session.query(Device).filter(Device.name == 'test').first()
        self.assertIsNotNone(device)
        expected = device.as_json()
        expected['app_name'] = 'TestApp'
        self.assertEqual(response, expected)

    def test_update_device_device_dne(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        walkoff.coredb.devicedb.device_db.session.add(device2)
        walkoff.coredb.devicedb.device_db.session.add(device1)
        walkoff.coredb.devicedb.device_db.session.commit()
        data = {'id': 404, 'name': 'renamed'}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                    status_code=OBJECT_DNE_ERROR, content_type='application/json')

    def test_update_device_app_dne(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        walkoff.coredb.devicedb.device_db.session.add(device2)
        walkoff.coredb.devicedb.device_db.session.add(device1)
        walkoff.coredb.devicedb.device_db.session.commit()
        data = {'id': device1.id, 'name': 'renamed', 'app_name': 'Invalid'}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                    status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_update_device_type_dne(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        walkoff.coredb.devicedb.device_db.session.add(app)
        walkoff.coredb.devicedb.device_db.session.commit()

        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        data = {'id': device1.id, 'name': 'renamed', 'app_name': self.test_app_name, 'type': 'Invalid'}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                    status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_update_device_invalid_fields(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        walkoff.coredb.devicedb.device_db.session.add(app)
        walkoff.coredb.devicedb.device_db.session.commit()

        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        fields_json = [{'name': 'test_name', 'value': 'invalid'}, {'name': 'test2', 'value': 'something'}]

        data = {'id': device1.id, 'name': 'renamed', 'app_name': self.test_app_name, 'type': 'test_type',
                'fields': fields_json}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                    status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def put_patch_update(self, verb):
        send_func = self.put_with_status_check if verb == 'put' else self.patch_with_status_check
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        walkoff.coredb.devicedb.device_db.session.add(app)
        walkoff.coredb.devicedb.device_db.session.commit()

        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        fields_json = [{'name': 'test_name', 'value': 123}, {'name': 'test2', 'value': 'something'}]

        data = {'id': device1.id, 'name': 'renamed', 'app_name': self.test_app_name, 'type': 'test_type',
                'fields': fields_json}
        send_func('/api/devices', headers=self.headers, data=json.dumps(data),
                                   status_code=SUCCESS, content_type='application/json')

        self.assertEqual(device1.name, 'renamed')
        self.assertEqual(device1.get_plaintext_fields(), {field['name']: field['value'] for field in fields_json})

    def test_update_device_fields_put(self):
        self.put_patch_update('put')

    def test_update_device_fields_patch(self):
        self.put_patch_update('patch')

    def test_export_apps_devices_no_filename(self):
        walkoff.config.config.load_app_apis(apps_path=tests.config.test_apps_path)

        fields = [{"name": "Text field", "value": "texts"}, {"name": "Encrypted field", "value": "encrypted"},
                  {"name": "Number field", "value": 5}, {"name": "Enum field", "value": "val 1"},
                  {"name": "Boolean field", "value": True}]
        data = {"name": "testDevice", "app_name": "HelloWorld", "type": "Test Device Type", "fields": fields}
        self.post_with_status_check('/api/devices', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type="application/json")

        self.post_with_status_check('/api/devices/export', headers=self.headers, content_type="application/json",
                                    data=json.dumps({}))

        self.assertIn('appdevice.json', os.listdir(tests.config.test_data_path))
        with open(walkoff.config.paths.default_appdevice_export_path, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            read_json = json.loads(read_file)
        self.assertIn('HelloWorld', read_json)
        self.assertTrue(len(read_json['HelloWorld']) >= 1)
        devices_read = 0
        for device in read_json['HelloWorld']:
            if device['name'] == 'testDevice':
                self.assertEqual(len(device['fields']), len(fields))
                for field in fields:
                    # Checks if test field is a subset of the device json fields
                    self.assertTrue(any(x for x in device['fields'] if set(x) not in set(
                        {k.encode("utf-8"): str(v).encode("utf-8") for k, v in field.items()})))
                devices_read += 1
        self.assertEqual(devices_read, 1)

    def test_export_apps_devices_with_filename(self):
        walkoff.config.config.load_app_apis(apps_path=tests.config.test_apps_path)

        fields = [{"name": "Text field", "value": "texts"}, {"name": "Encrypted field", "value": "encrypted"},
                  {"name": "Number field", "value": 5}, {"name": "Enum field", "value": "val 1"},
                  {"name": "Boolean field", "value": True}]
        data = {"name": "testDevice", 'app_name': "HelloWorld", "type": "Test Device Type", "fields": fields}
        self.post_with_status_check('/api/devices', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type="application/json")

        filename = 'testappdevices.json'
        filepath = os.path.join(tests.config.test_data_path, filename)
        data = {'filename': filepath}
        self.post_with_status_check('/api/devices/export',
                                    data=json.dumps(data), headers=self.headers, content_type="application/json")

        self.assertIn(filename, os.listdir(tests.config.test_data_path))
        with open(filepath, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            read_json = json.loads(read_file)
        self.assertIn('HelloWorld', read_json)
        self.assertTrue(len(read_json['HelloWorld']) >= 1)
        devices_read = 0
        for device in read_json['HelloWorld']:
            if device['name'] == 'testDevice':
                self.assertEqual(len(device['fields']), len(fields))
                for field in fields:
                    # self.assertIn(field, device['fields'])
                    # Checks if test field is a subset of the device json fields
                    self.assertTrue(any(x for x in device['fields'] if set(x) not in set(
                        {k.encode("utf-8"): str(v).encode("utf-8") for k, v in field.items()})))
                devices_read += 1
        self.assertEqual(devices_read, 1)

    def test_import_apps_devices(self):
        walkoff.config.config.load_app_apis(apps_path=tests.config.test_apps_path)

        fields = [{"name": "Text field", "value": "texts"}, {"name": "Encrypted field", "value": "encrypted"},
                  {"name": "Number field", "value": 5}, {"name": "Enum field", "value": "val 1"},
                  {"name": "Boolean field", "value": True}]
        data = {"name": "testDevice", 'app_name': "HelloWorld", "type": "Test Device Type", "fields": fields}
        self.post_with_status_check('/api/devices', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type="application/json")

        filename = 'testappdevices.json'
        filepath = os.path.join(tests.config.test_data_path, filename)
        data = {'filename': filepath}
        self.post_with_status_check('/api/devices/export',
                                    data=json.dumps(data), headers=self.headers, content_type="application/json")

        fields.remove({"name": "Encrypted field", "value": "encrypted"})
        fields.append({"name": "Encrypted field", "encrypted": True})

        dev = walkoff.coredb.devicedb.device_db.session.query(Device).filter(Device.name == "testDevice").first()
        walkoff.coredb.devicedb.device_db.session.delete(dev)
        walkoff.coredb.devicedb.device_db.session.commit()

        self.get_with_status_check('/api/devices/import',
                                   data=json.dumps(data), headers=self.headers, content_type="application/json")

        app = walkoff.coredb.devicedb.device_db.session.query(App).filter(App.name == "HelloWorld").first()
        app_id = app.id
        devices = walkoff.coredb.devicedb.device_db.session.query(Device).all()
        for device in devices:
            if device.name == 'testDevice':
                device_json = device.as_json()
                self.assertEqual(device.app_id, app_id)
                self.assertEqual(len(device_json['fields']), len(fields))
                for field in fields:
                    # self.assertIn(field, device_json['fields'])
                    # Checks if test field is a subset of the device json fields
                    self.assertTrue(any(x for x in device_json['fields'] if set(x) not in set(
                        {k.encode("utf-8"): str(v).encode("utf-8") for k, v in field.items()})))
