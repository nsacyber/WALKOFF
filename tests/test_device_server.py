from tests.util.servertestcase import ServerTestCase
import json
from server.appdevice import Device, App, DeviceField
from server.database import db
from server.returncodes import *
import core.config.config
from server.endpoints.devices import remove_configuration_keys_from_device_json


class TestDevicesServer(ServerTestCase):
    def setUp(self):
        self.test_app_name = 'TestApp'

    def tearDown(self):
        db.session.rollback()
        for device in Device.query.all():
            db.session.delete(device)
        for field in DeviceField.query.all():
            db.session.delete(field)
        app = App.query.filter_by(name=self.test_app_name).first()
        if app is not None:
            db.session.delete(app)
        db.session.commit()
        core.config.config.app_apis = {}

    def test_read_all_devices_no_devices_in_db(self):
        response = self.get_with_status_check('/api/devices', headers=self.headers, status_code=SUCCESS)
        self.assertListEqual(response, [])

    def test_read_all_devices(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        db.session.add(app)
        db.session.commit()
        response = self.get_with_status_check('/api/devices', headers=self.headers, status_code=SUCCESS)
        expected_device1 = device1.as_json()
        expected_device1['app'] = 'TestApp'
        expected_device2 = device2.as_json()
        expected_device2['app'] = 'TestApp'
        self.assertIn(expected_device1, response)
        self.assertIn(expected_device2, response)

    def test_read_device(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        db.session.add(device2)
        db.session.add(device1)
        db.session.commit()
        response = self.get_with_status_check('/api/devices/{}'.format(device1.id), headers=self.headers,
                                              status_code=SUCCESS)
        expected_device1 = device1.as_json()
        expected_device1['app'] = ''
        self.assertEqual(response, expected_device1)

    def test_read_device_does_not_exist(self):
        self.get_with_status_check('/api/devices/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_delete_device(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        db.session.add(device2)
        db.session.add(device1)
        db.session.commit()
        device1_id = device1.id
        self.delete_with_status_check('/api/devices/{}'.format(device1_id), headers=self.headers, status_code=SUCCESS)
        self.assertIsNone(Device.query.filter_by(id=device1_id).first())

    def test_delete_device_device_dne(self):
        self.delete_with_status_check('/api/devices/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_create_device_device_already_exists(self):
        device1 = Device('test', [], [], 'type', description='description')
        db.session.add(device1)
        db.session.commit()
        device_json = {'app': 'test', 'name': 'test', 'type': 'some_type', 'fields': []}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=OBJECT_EXISTS_ERROR, content_type='application/json')

    def test_create_device_app_not_in_apis(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        core.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app': 'Invalid', 'name': 'test', 'type': 'some_type', 'fields': []}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device_device_type_does_not_exist(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        core.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app': 'TestApp', 'name': 'test', 'type': 'invalid', 'fields': []}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device_invalid_fields(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        core.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app': 'TestApp', 'name': 'test', 'type': 'test_type',
                       'fields': [{'name': 'test_name', 'value': 'invalid'}, {'name': 'test2', 'value': 'something'}]}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device_app_not_in_db(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        core.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        device_json = {'app': 'TestApp', 'name': 'test', 'type': 'test_type',
                       'fields': [{'name': 'test_name', 'value': 123}, {'name': 'test2', 'value': 'something'}]}
        self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_create_device(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        core.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}
        app = App(name=self.test_app_name)
        db.session.add(app)
        db.session.commit()

        device_json = {'app': 'TestApp', 'name': 'test', 'type': 'test_type',
                       'fields': [{'name': 'test_name', 'value': 123}, {'name': 'test2', 'value': 'something'}]}
        response = self.put_with_status_check('/api/devices', headers=self.headers, data=json.dumps(device_json),
                                   status_code=OBJECT_CREATED, content_type='application/json')
        device = Device.query.filter_by(name='test').first()
        self.assertIsNotNone(device)
        expected = device.as_json()
        expected['app'] = 'TestApp'
        remove_configuration_keys_from_device_json(expected)
        self.assertEqual(response, expected)

    def test_update_device_device_dne(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        db.session.add(device2)
        db.session.add(device1)
        db.session.commit()
        data = {'id': 404, 'name': 'renamed'}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                              status_code=OBJECT_DNE_ERROR, content_type='application/json')

    def test_update_device_app_dne(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        db.session.add(device2)
        db.session.add(device1)
        db.session.commit()
        data = {'id': device1.id, 'name': 'renamed', 'app': 'Invalid'}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                              status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_update_device_type_dne(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        db.session.add(app)
        db.session.commit()

        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        core.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        data = {'id': device1.id, 'name': 'renamed', 'app': self.test_app_name, 'type': 'Invalid'}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                              status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_update_device_invalid_fields(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        db.session.add(app)
        db.session.commit()

        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        core.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        fields_json = [{'name': 'test_name', 'value': 'invalid'}, {'name': 'test2', 'value': 'something'}]

        data = {'id': device1.id, 'name': 'renamed', 'app': self.test_app_name, 'type': 'test_type', 'fields': fields_json}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                              status_code=INVALID_INPUT_ERROR, content_type='application/json')

    def test_update_device_fields(self):
        device1 = Device('test', [], [], 'type')
        device2 = Device('test2', [], [], 'type')
        app = App(name=self.test_app_name, devices=[device1, device2])
        db.session.add(app)
        db.session.commit()

        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        core.config.config.app_apis = {self.test_app_name: {'devices': {'test_type': {'fields': fields_json}}}}

        fields_json = [{'name': 'test_name', 'value': 123}, {'name': 'test2', 'value': 'something'}]

        data = {'id': device1.id, 'name': 'renamed', 'app': self.test_app_name, 'type': 'test_type', 'fields': fields_json}
        self.post_with_status_check('/api/devices', headers=self.headers, data=json.dumps(data),
                                              status_code=SUCCESS, content_type='application/json')

        self.assertEqual(device1.name, 'renamed')
        self.assertEqual(device1.get_plaintext_fields(), {field['name']: field['value'] for field in fields_json})
