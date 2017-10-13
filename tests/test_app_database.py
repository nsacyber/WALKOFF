import unittest
from server.appdevice import App, Device


class TestAppDatabase(unittest.TestCase):

    def setUp(self):
        self.device1 = Device('test1', [], [], 'type1')
        self.device2 = Device('test2', [], [], 'type1')
        self.device3 = Device('test3', [], [], 'type2')
        self.device4 = Device('test4', [], [], 'type2')
        self.all_devices = [self.device1, self.device2, self.device3, self.device4]

    def assertConstructionIsCorrect(self, app, name, devices):
        self.assertEqual(app.name, name)
        self.assertSetEqual({device.name for device in app.devices}, devices)

    def test_init_name_only(self):
        app = App('test')
        self.assertConstructionIsCorrect(app, 'test', set())

    def test_init_with_devices(self):
        app = App('test', devices=self.all_devices)
        self.assertConstructionIsCorrect(app, 'test', {'test1', 'test2', 'test3', 'test4'})

    def test_get_device(self):
        app = App('test', devices=self.all_devices)
        self.assertEqual(app.get_device('test2').as_json(), self.device2.as_json())

    def test_get_device_invalid(self):
        app = App('test', devices=self.all_devices)
        self.assertIsNone(app.get_device('invalid'))

    def test_as_json(self):
        app = App('test', devices=self.all_devices)
        app_json = app.as_json(with_devices=True)
        self.assertEqual(app_json['name'], 'test')
        expected_devices_json = [device.as_json() for device in app.devices]
        for device in app_json['devices']:
            self.assertIn(device, expected_devices_json)

    def test_add_device(self):
        app = App('test', devices=[self.device1, self.device2, self.device3])
        app.add_device(self.device4)
        self.assertSetEqual({device.name for device in app.devices}, {'test1', 'test2', 'test3', 'test4'})

    def test_add_device_already_exists(self):
        app = App('test', devices=[self.device1, self.device2, self.device3])
        app.add_device(self.device3)
        self.assertSetEqual({device.name for device in app.devices}, {'test1', 'test2', 'test3'})