import json
import os

import walkoff.config
from tests.util.servertestcase import ServerTestCase
from walkoff.executiondb.device import Device, App, DeviceField, EncryptedDeviceField
from walkoff.server.returncodes import *


class TestDevicesServer(ServerTestCase):
    def setUp(self):
        self.test_app_name = 'TestApp'

    def tearDown(self):
        self.app.running_context.execution_db.session.rollback()
        for device in self.app.running_context.execution_db.session.query(Device).all():
            self.app.running_context.execution_db.session.delete(device)
        self.app.running_context.execution_db.session.commit()
        for field in self.app.running_context.execution_db.session.query(DeviceField).all():
            self.app.running_context.execution_db.session.delete(field)
        for field in self.app.running_context.execution_db.session.query(EncryptedDeviceField).all():
            self.app.running_context.execution_db.session.delete(field)
        app = self.app.running_context.execution_db.session.query(App).filter(App.name == self.test_app_name).first()
        if app is not None:
            self.app.running_context.execution_db.session.delete(app)
        self.app.running_context.execution_db.session.commit()
        walkoff.config.app_apis = {}
        if os.path.exists(os.path.join(walkoff.config.Config.APPS_PATH, 'testDevice.json')):
            os.remove(os.path.join(walkoff.config.Config.APPS_PATH, 'testDevice.json'))

    def test_read_all_devices_no_devices_in_db(self):
        response = self.get_with_status_check('/api/devices', headers=self.headers, status_code=SUCCESS)
        self.assertListEqual(response, [])

    def test_read_all_devices(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        self.app.running_context.execution_db.session.add(app)
        self.app.running_context.execution_db.session.commit()
        response = self.get_with_status_check('/api/devices?page=1', headers=self.headers, status_code=SUCCESS)
        expected_device1 = device1.as_json()
        expected_device1['app_name'] = 'TestApp'
        expected_device2 = device2.as_json()
        expected_device2['app_name'] = 'TestApp'
        self.assertIn(expected_device1, response)
        self.assertIn(expected_device2, response)

    def test_read_device(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        self.app.running_context.execution_db.session.add(device2)
        self.app.running_context.execution_db.session.add(device1)
        self.app.running_context.execution_db.session.commit()
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
        self.app.running_context.execution_db.session.add(device2)
        self.app.running_context.execution_db.session.add(device1)
        self.app.running_context.execution_db.session.commit()
        device1_id = device1.id
        self.delete_with_status_check('/api/devices/{}'.format(device1_id), headers=self.headers,
                                      status_code=NO_CONTENT)
        self.assertIsNone(
            self.app.running_context.execution_db.session.query(Device).filter(Device.id == device1_id).first())

    def test_delete_device_device_dne(self):
        self.delete_with_status_check('/api/devices/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_create_device_device_already_exists(self):
        device1 = Device('test', [], [], 'type', description='description')
        self.app.running_context.execution_db.session.add(device1)
        self.app.running_context.execution_db.session.commit()
        device_json = {'app_name': 'test', 'name': 'test', 'type': 'some_type', 'fields': []}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                    status_code=OBJECT_EXISTS_ERROR, content_type='application/json')

    def test_create_device_app_not_in_apis(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app_name': 'Invalid', 'name': 'test', 'type': 'some_type', 'fields': []}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                    status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device_device_type_does_not_exist(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app_name': 'TestApp', 'name': 'test', 'type': 'invalid', 'fields': []}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                    status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device_invalid_fields(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app_name': 'TestApp', 'name': 'test', 'type': 'test_type',
                       'fields': [{'name': 'test_name', 'value': 'invalid'}, {'name': 'test2', 'value': 'something'}]}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                    status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device_app_not_in_db(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app_name': 'TestApp', 'name': 'test', 'type': 'test_type',
                       'fields': [{'name': 'test_name', 'value': 123}, {'name': 'test2', 'value': 'something'}]}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                    status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}
        app = App(name=self.test_app_name)
        self.app.running_context.execution_db.session.add(app)
        self.app.running_context.execution_db.session.commit()

        device_json = {'app_name': 'TestApp', 'name': 'test', 'type': 'test_type',
                       'fields': [{'name': 'test_name', 'value': 123}, {'name': 'test2', 'value': 'something'}]}
        response = self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                               status_code=OBJECT_CREATED, content_type='application/json')
        device = self.app.running_context.execution_db.session.query(Device).filter(Device.name == 'test').first()
        self.assertIsNotNone(device)
        expected = device.as_json()
        expected['app_name'] = 'TestApp'
        self.assertEqual(response, expected)

    def test_update_device_device_dne(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        self.app.running_context.execution_db.session.add(device2)
        self.app.running_context.execution_db.session.add(device1)
        self.app.running_context.execution_db.session.commit()
        data = {'id': 404, 'name': 'renamed'}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                   status_code=OBJECT_DNE_ERROR, content_type='application/json')

    def test_update_device_app_dne(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        self.app.running_context.execution_db.session.add(device2)
        self.app.running_context.execution_db.session.add(device1)
        self.app.running_context.execution_db.session.commit()
        data = {'id': device1.id, 'name': 'renamed', 'app_name': 'Invalid'}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_update_device_type_dne(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        self.app.running_context.execution_db.session.add(app)
        self.app.running_context.execution_db.session.commit()

        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        data = {'id': device1.id, 'name': 'renamed', 'app_name': self.test_app_name, 'type': 'Invalid'}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_update_device_invalid_fields(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        self.app.running_context.execution_db.session.add(app)
        self.app.running_context.execution_db.session.commit()

        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

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
        self.app.running_context.execution_db.session.add(app)
        self.app.running_context.execution_db.session.commit()

        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

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

    def test_export_apps_devices(self):
        walkoff.config.load_app_apis(apps_path=walkoff.config.Config.APPS_PATH)

        fields = [{"name": "Text field", "value": "texts"}, {"name": "Encrypted field", "value": "encrypted"},
                  {"name": "Number field", "value": 5}, {"name": "Enum field", "value": "val 1"},
                  {"name": "Boolean field", "value": True}]
        data = {"name": "testDevice", "app_name": "HelloWorld", "type": "Test Device Type", "fields": fields}
        response = self.post_with_status_check('/api/devices', data=json.dumps(data), headers=self.headers,
                                               status_code=OBJECT_CREATED, content_type="application/json")

        device = self.get_with_status_check('/api/devices/{}?mode=export'.format(response['id']),
                                            headers=self.headers)

        self.assertEqual(device['name'], 'testDevice')
        self.assertEqual(device['app_name'], 'HelloWorld')
        self.assertEqual(device['type'], 'Test Device Type')
        self.assertEqual(len(device['fields']), len(fields))
        for field in fields:
            # Checks if test field is a subset of the device json fields
            self.assertTrue(any(x for x in device['fields'] if set(x) not in set(
                {k.encode("utf-8"): str(v).encode("utf-8") for k, v in field.items()})))

    def test_import_apps_devices(self):
        walkoff.config.load_app_apis(apps_path=walkoff.config.Config.APPS_PATH)

        fields = [{"name": "Text field", "value": "texts"}, {"name": "Number field", "value": 5},
                  {"name": "Enum field", "value": "val 1"}, {"name": "Boolean field", "value": True}]
        data = {"name": "testDevice", 'app_name': "HelloWorld", "type": "Test Device Type 3", "fields": fields}
        response = self.post_with_status_check('/api/devices', data=json.dumps(data), headers=self.headers,
                                               status_code=OBJECT_CREATED, content_type="application/json")

        device = self.get_with_status_check('/api/devices/{}?mode=export'.format(response['id']),
                                            headers=self.headers)
        device.pop('id', None)
        for field in device['fields']:
            field.pop('id', None)

        path = os.path.join(walkoff.config.Config.APPS_PATH, 'testDevice.json')
        with open(path, 'w') as f:
            f.write(json.dumps(device, indent=4, sort_keys=True))

        dev = self.app.running_context.execution_db.session.query(Device).filter(Device.name == "testDevice").first()
        self.app.running_context.execution_db.session.delete(dev)
        self.app.running_context.execution_db.session.commit()

        files = {'file': (path, open(path, 'r'), 'application/json')}
        device = self.post_with_status_check('/api/devices', headers=self.headers, status_code=OBJECT_CREATED,
                                             data=files, content_type='multipart/form-data')

        self.assertEqual(device['name'], 'testDevice')
        self.assertEqual(device['app_name'], 'HelloWorld')
        self.assertEqual(device['type'], 'Test Device Type 3')
        self.assertEqual(len(device['fields']), len(fields))
        for field in fields:
            # Checks if test field is a subset of the device json fields
            self.assertTrue(any(x for x in device['fields'] if set(x) not in set(
                {k.encode("utf-8"): str(v).encode("utf-8") for k, v in field.items()})))

    def test_device_pagination(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        walkoff.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}
        app = App(name=self.test_app_name)
        self.app.running_context.execution_db.session.add(app)
        self.app.running_context.execution_db.session.commit()

        for i in range(40):
            device_json = {'app_name': 'TestApp', 'name': str(i), 'type': 'test_type',
                           'fields': [{'name': 'test_name', 'value': 123}, {'name': 'test2', 'value': 'something'}]}
            self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                        status_code=OBJECT_CREATED, content_type='application/json')

        response = self.get_with_status_check('/api/devices?page=1', headers=self.headers, status_code=SUCCESS)
        self.assertEqual(len(response), 20)
        devices = [str(i) for i in range(20)]
        for device in response:
            self.assertIn(device['name'], devices)
        response = self.get_with_status_check('/api/devices?page=2', headers=self.headers, status_code=SUCCESS)
        self.assertEqual(len(response), 20)
        devices = [str(i) for i in range(20, 40)]
        for device in response:
            self.assertIn(device['name'], devices)
        response = self.get_with_status_check('/api/devices?page=3', headers=self.headers, status_code=SUCCESS)
        self.assertEqual(len(response), 0)
