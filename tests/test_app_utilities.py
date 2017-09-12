import unittest
from server.database import db
from server.appdevice import get_device, get_all_devices_for_app, get_all_devices_of_type_from_app, App, Device
import server.flaskserver


class TestAppUtilities(unittest.TestCase):

    def setUp(self):
        self.app_name = 'TestApp'
        self.app = server.flaskserver.app.test_client(self)
        self.app.testing = True

        self.context = server.flaskserver.app.test_request_context()
        self.context.push()

        self.device1 = Device('test1', [], [], 'type1')
        self.device2 = Device('test2', [], [], 'type1')
        self.device3 = Device('test3', [], [], 'type2')
        self.device4 = Device('test4', [], [], 'type2')

    def tearDown(self):
        db.session.rollback()
        app = App.query.filter_by(name=self.app_name).first()
        if app is not None:
            db.session.delete(app)
        for device in Device.query.all():
            db.session.delete(device)
        db.session.commit()

    def add_test_app(self, devices=None):
        devices = devices if devices is not None else []
        app = App(self.app_name, devices=devices)
        db.session.add(app)
        db.session.commit()

    def test_get_all_devices_for_app_dne(self):
        self.assertListEqual(get_all_devices_for_app('invalid'), [])

    def test_get_all_devices_for_app_no_devices(self):
        self.add_test_app()
        self.assertListEqual(get_all_devices_for_app(self.app_name), [])

    def test_get_all_devices_for_app(self):
        devices = [self.device1, self.device2, self.device3]
        self.add_test_app(devices=devices)
        self.assertListEqual(get_all_devices_for_app(self.app_name), devices)

    def test_get_all_devices_of_type_app_dne(self):
        self.assertListEqual(get_all_devices_of_type_from_app('invalid', 'type1'), [])

    def test_get_all_devices_of_type_no_devices(self):
        self.add_test_app()
        self.assertListEqual(get_all_devices_of_type_from_app(self.app_name, 'type1'), [])

    def test_get_all_devices_of_type_no_type(self):
        devices = [self.device1, self.device2]
        self.add_test_app(devices=devices)
        self.assertListEqual(get_all_devices_of_type_from_app(self.app_name, 'type2'), [])

    def test_get_all_devices_of_type(self):
        devices = [self.device1, self.device2, self.device3, self.device4]
        self.add_test_app(devices=devices)
        self.assertListEqual(get_all_devices_of_type_from_app(self.app_name, 'type1'), [self.device1, self.device2])

    def test_get_device_app_dne(self):
        self.assertIsNone(get_device('invalid', 'test1'))

    def test_get_device_no_devices(self):
        self.add_test_app()
        self.assertIsNone(get_device(self.app_name, 'test1'))

    def test_get_device_no_matching_device(self):
        devices = [self.device1, self.device2, self.device3, self.device4]
        self.add_test_app(devices=devices)
        self.assertIsNone(get_device(self.app_name, 'invalid'))

    def test_get_device(self):
        devices = [self.device1, self.device2, self.device3, self.device4]
        self.add_test_app(devices=devices)
        self.assertEqual(get_device(self.app_name, 'test1'), self.device1)
