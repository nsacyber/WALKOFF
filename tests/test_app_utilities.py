import unittest
from server import flaskserver
from server.appdevice import App
from tests.util.assertwrappers import orderless_list_compare


class TestAppUtilities(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        with flaskserver.running_context.flask_app.app_context():
            flaskserver.running_context.Device.query.delete()
            flaskserver.running_context.App.query.delete()
            flaskserver.database.db.session.commit()

    @classmethod
    def tearDownClass(cls):
        # reset the app database table for other tests
        from server.app import create_test_data
        with flaskserver.running_context.flask_app.app_context():
            create_test_data()

    def test_get_all_devices_for_nonexistent_app_empty_db(self):
        self.assertListEqual(App.get_all_devices_for_app('non-existent-app'), [])

    def test_get_all_devices_for_nonexistent_app_full_db(self):
        for app_name in ['App1', 'App2', 'App3']:
            flaskserver.running_context.db.session.add(flaskserver.running_context.App(app=app_name, devices=[]))
        flaskserver.running_context.db.session.commit()
        self.assertListEqual(App.get_all_devices_for_app('App4'), [])

    def test_get_all_devices_for_existing_app_with_devices(self):
        devices = ['dev1', 'dev2', '', 'dev3']
        flaskserver.running_context.db.session.add(flaskserver.running_context.App(app='App1', devices=devices))
        flaskserver.running_context.db.session.commit()
        orderless_list_compare(self, [device.name for device in App.get_all_devices_for_app('App1')], devices)

    def test_get_all_devices_for_existing_app_with_no_devices(self):
        flaskserver.running_context.db.session.add(flaskserver.running_context.App(app='App1', devices=[]))
        flaskserver.running_context.db.session.commit()
        self.assertListEqual(App.get_all_devices_for_app('App1'), [])

    def test_get_device_for_nonexistent_app_and_device_empty_db(self):
        self.assertIsNone(App.get_device('non-existent-app', 'nonexistent-device'))

    @staticmethod
    def __setup_database():
        flaskserver.running_context.db.session.add(flaskserver.running_context.App(app='App1', devices=[]))
        flaskserver.running_context.db.session.add(flaskserver.running_context.App(app='App2', devices=['a', 'b']))
        flaskserver.running_context.db.session.add(flaskserver.running_context.App(app='App3', devices=['a', 'c', 'd']))
        flaskserver.running_context.db.session.commit()

    def test_get_device_for_nonexistent_app_device(self):
        self.__setup_database()
        self.assertIsNone(App.get_device('non-existent-app', 'nonexistent-device'))

    def test_get_device_for_nonexistent_app_existing_device(self):
        self.__setup_database()
        for device_name in ['a', 'b', 'c', 'd']:
            self.assertIsNone(App.get_device('non-existent-app', device_name))

    def test_get_device_for_existent_app_nonexistent_device(self):
        self.__setup_database()
        for app_name in ['App1', 'App2', 'App3']:
            self.assertIsNone(App.get_device(app_name, 'non-existent-device'))

    def test_get_device_for_existent_app_no_devices(self):
        self.__setup_database()
        for device_name in ['a', 'b', 'c', 'd']:
            self.assertIsNone(App.get_device('App1', device_name))

    def test_get_device_for_existent_app_with_devices(self):
        self.__setup_database()
        app_devices = {'App2': ['a', 'b'],
                       'App3': ['a', 'c', 'd']}
        for app_name, devices in app_devices.items():
            for device_name in devices:
                device = App.get_device(app_name, device_name)
                self.assertIsInstance(device, flaskserver.running_context.Device)
                self.assertEqual(device.name, device_name)
