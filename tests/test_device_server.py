from tests.util.servertestcase import ServerTestCase
import json
from server.appdevice import Device, App
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
        app = App.query.filter_by(name=self.test_app_name).first()
        if app is not None:
            db.session.delete(app)
        db.session.commit()
        core.config.config.app_apis = {}

    def test_read_all_devices_no_devices_in_db(self):
        response = self.get_with_status_check('/api/devices', headers=self.headers, status_code=SUCCESS)
        self.assertListEqual(response, [])

    def test_read_all_devices(self):
        fields_json1 = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': False},
                        {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': False}]
        device1 = Device('test', fields_json1, 'type')
        fields_json2 = [{'name': 'test_name', 'type': 'integer', 'value': 401, 'encrypted': False},
                        {'name': 'test2', 'type': 'boolean', 'value': True, 'encrypted': False}]
        device2 = Device('test2', fields_json2, 'type')
        db.session.add(device1)
        db.session.add(device2)
        response = self.get_with_status_check('/api/devices', headers=self.headers, status_code=SUCCESS)
        self.assertIn(device1.as_json(), response)
        self.assertIn(device2.as_json(), response)

    def test_read_device(self):
        fields_json1 = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': False},
                        {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': False}]
        device1 = Device('test', fields_json1, 'type')
        fields_json2 = [{'name': 'test_name', 'type': 'integer', 'value': 401, 'encrypted': False},
                        {'name': 'test2', 'type': 'boolean', 'value': True, 'encrypted': False}]
        device2 = Device('test2', fields_json2, 'type')
        db.session.add(device2)
        db.session.add(device1)
        db.session.commit()
        response = self.get_with_status_check('/api/devices/{}'.format(device1.id), headers=self.headers,
                                              status_code=SUCCESS)
        self.assertEqual(response, device1.as_json())

    def test_read_device_does_not_exist(self):
        self.get_with_status_check('/api/devices/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_delete_device(self):
        fields_json1 = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': False},
                        {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': False}]
        device1 = Device('test', fields_json1, 'type')
        fields_json2 = [{'name': 'test_name', 'type': 'integer', 'value': 401, 'encrypted': False},
                        {'name': 'test2', 'type': 'boolean', 'value': True, 'encrypted': False}]
        device2 = Device('test2', fields_json2, 'type')
        db.session.add(device2)
        db.session.add(device1)
        db.session.commit()
        device1_id = device1.id
        self.delete_with_status_check('/api/devices/{}'.format(device1_id), headers=self.headers, status_code=SUCCESS)
        self.assertIsNone(Device.query.filter_by(id=device1_id).first())

    def test_delete_device_device_dne(self):
        self.delete_with_status_check('/api/devices/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_create_device_device_already_exists(self):
        fields_json1 = [{'name': 'test_name', 'type': 'integer', 'value': 123, 'encrypted': False},
                        {'name': 'test2', 'type': 'string', 'value': 'something', 'encrypted': False}]
        device1 = Device('test', fields_json1, 'type', description='description')
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
        remove_configuration_keys_from_device_json(expected)
        self.assertEqual(response, expected)


