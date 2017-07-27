import json
import os
from tests.util.servertestcase import ServerTestCase
from server import flaskserver as server
import tests.config
import core.config.paths
from server.return_codes import *
import pyaes


class TestAppsAndDevices(ServerTestCase):
    def setUp(self):
        self.name = "testDevice"

        self.username = "testUsername"
        self.password = "testPassword"
        self.ip = "127.0.0.1"
        self.port = 6000

        self.extraFields = {"extraFieldOne": "extraNameOne", "extraFieldTwo": "extraNameTwo"}

    def tearDown(self):
        with server.running_context.flask_app.app_context():
            server.running_context.Device.query.filter_by(name=self.name).delete()
            server.running_context.Device.query.filter_by(name="testDeviceTwo").delete()
            server.database.db.session.commit()

    def test_add_device(self):
        data = {"name": self.name, "username": self.username, "password": self.password, "ip": self.ip, "port": self.port,
                "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}
        self.put_with_status_check('/api/devices',
                                   data=json.dumps(data),
                                   headers=self.headers,
                                   status_code=OBJECT_CREATED,
                                   content_type="application/json")
        self.put_with_status_check('/api/devices',
                                   error='Device already exists.',
                                   data=json.dumps(data),
                                   headers=self.headers,
                                   status_code=OBJECT_EXISTS_ERROR,
                                   content_type="application/json")

    def test_display_device(self):
        data = {"name": self.name, "username": self.username, "password": self.password, "ip": self.ip, "port": self.port,
                "extraFields": str(self.extraFields), "app": "HelloWorld"}
        response = self.put_with_status_check('/api/devices', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type="application/json")

        dev_id = response['id']

        response = json.loads(self.app.get('/api/devices/'+dev_id, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["username"], self.username)
        self.assertEqual(response["name"], self.name)
        self.assertEqual(response["ip"], self.ip)
        self.assertEqual(response["port"], str(self.port))
        self.assertEqual(response["extraFieldOne"], "extraNameOne")
        self.assertEqual(response["extraFieldTwo"], "extraNameTwo")

    def test_edit_device(self):
        data = {"name": self.name, "username": self.username, "password": self.password, "ip": self.ip, "port": self.port,
                "extraFields": str(self.extraFields), "app": "HelloWorld"}

        response = self.put_with_status_check('/api/devices', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type="application/json")
        dev_id = response['id']
        data = {"ip": "192.168.196.1", "id": int(dev_id)}
        self.post_with_status_check('/api/devices',
                                    data=json.dumps(data), headers=self.headers, content_type="application/json")

        data = {"port": 6001, "id": int(dev_id)}
        self.post_with_status_check('/api/devices',
                                    data=json.dumps(data), headers=self.headers, content_type="application/json")

        data = {"extraFields": json.dumps({"extraFieldOne": "extraNameOneOne"}), "id": int(dev_id)}
        self.post_with_status_check('/api/devices',
                                    data=json.dumps(data), headers=self.headers, content_type="application/json")

        response = json.loads(
            self.app.get('/api/devices/'+dev_id, headers=self.headers, content_type="application/json").get_data(
                as_text=True))
        self.assertEqual(response["extraFieldOne"], "extraNameOneOne")

    def test_add_and_display_multiple_devices(self):
        data = {"name": self.name, "username": self.username, "password": self.password, "ip": self.ip, "port": self.port,
                "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}
        self.put_with_status_check('/api/devices', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type='application/json')

        data = {"name": "testDeviceTwo", "username": self.username, "password": self.password, "ip": self.ip,
                "port": self.port, "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}

        self.put_with_status_check('/api/devices', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type="application/json")

        response = self.get_with_status_check('/api/devices', headers=self.headers, data=json.dumps({}),
                                              content_type="application/json")

        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]["name"], self.name)
        self.assertEqual(response[1]["name"], "testDeviceTwo")
        self.assertEqual(response[0]["app"]["name"], response[1]["app"]["name"])

    def test_export_apps_devices_no_filename(self):
        data = {"name": self.name, "username": self.username, "passwrd": self.password, "ip": self.ip, "port": self.port,
                "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}
        self.put_with_status_check('/api/devices',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
                                   content_type = "application/json")
        data = {"name": "testDeviceTwo", "username": self.username, "password": self.password, "ip": self.ip,
                "port": self.port, "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}

        self.put_with_status_check('/api/devices',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
                                   content_type="application/json")

        test_device_one_json = {"extraFieldOne": "extraNameOne",
                                "extraFieldTwo": "extraNameTwo",
                                "ip": "127.0.0.1",
                                "name": "testDevice",
                                "port": "6000",
                                "username": "testUsername"}
        test_device_two_json = {"extraFieldOne": "extraNameOne",
                                "extraFieldTwo": "extraNameTwo",
                                "ip": "127.0.0.1",
                                "name": "testDeviceTwo",
                                "port": "6000",
                                "username": "testUsername"}

        self.post_with_status_check('/api/devices/export', headers=self.headers, content_type="application/json",
                                    data=json.dumps({}))
        self.assertIn('appdevice.json', os.listdir(tests.config.test_data_path))
        with open(core.config.paths.default_appdevice_export_path, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            read_json = json.loads(read_file)
        self.assertIn('HelloWorld', read_json)
        self.assertTrue(len(read_json['HelloWorld']) >= 2)
        devices_read = 0
        for device in read_json['HelloWorld']:
            if device['name'] == 'testDevice':
                self.assertDictEqual(device, test_device_one_json)
                devices_read += 1
            elif device['name'] == 'testDeviceTwo':
                self.assertDictEqual(device, test_device_two_json)
                devices_read += 1
        self.assertEqual(devices_read, 2)

    def test_export_apps_devices_with_filename(self):
        data = {"name": self.name, "username": self.username, "password": self.password, "ip": self.ip,
                "port": self.port, "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}

        self.put_with_status_check('/api/devices',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")

        data = {"name": "testDeviceTwo", "username": self.username, "password": self.password, "ip": self.ip,
                "port": self.port, "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}

        self.put_with_status_check('/api/devices',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED, content_type = "application/json")
        test_device_one_json = {"extraFieldOne": "extraNameOne",
                                "extraFieldTwo": "extraNameTwo",
                                "ip": "127.0.0.1",
                                "name": "testDevice",
                                "port": "6000",
                                "username": "testUsername"}
        test_device_two_json = {"extraFieldOne": "extraNameOne",
                                "extraFieldTwo": "extraNameTwo",
                                "ip": "127.0.0.1",
                                "name": "testDeviceTwo",
                                "port": "6000",
                                "username": "testUsername"}
        filename = 'testappdevices.json'
        filepath = os.path.join(tests.config.test_data_path, filename)
        data = {'filename': filepath}
        self.post_with_status_check('/api/devices/export',
                                    data=json.dumps(data), headers=self.headers, content_type = "application/json")
        self.assertIn(filename, os.listdir(tests.config.test_data_path))
        with open(filepath, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            read_json = json.loads(read_file)
        self.assertIn('HelloWorld', read_json)
        self.assertTrue(len(read_json['HelloWorld']) >= 2)
        devices_read = 0
        for device in read_json['HelloWorld']:
            if device['name'] == 'testDevice':
                self.assertDictEqual(device, test_device_one_json)
                devices_read += 1
            elif device['name'] == 'testDeviceTwo':
                self.assertDictEqual(device, test_device_two_json)
                devices_read += 1
        self.assertEqual(devices_read, 2)

    def test_import_apps_devices(self):
        data = {"name": self.name, "username": self.username, "password": self.password, "ip": self.ip,
                "port": self.port, "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}
        self.put_with_status_check('/api/devices',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED, content_type = "application/json")

        data = {"name": "testDeviceTwo", "username": self.username, "password": self.password, "ip": self.ip,
                "port": self.port, "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}

        self.put_with_status_check('/api/devices',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED, content_type = "application/json")

        test_device_one_json = {"extraFieldOne": "extraNameOne",
                                "extraFieldTwo": "extraNameTwo",
                                "ip": "127.0.0.1",
                                "name": "testDevice",
                                "port": "6000",
                                "username": "testUsername",
                                'app': {"name": "HelloWorld"}
                                }
        test_device_two_json = {"extraFieldOne": "extraNameOne",
                                "extraFieldTwo": "extraNameTwo",
                                "ip": u"127.0.0.1",
                                "name": "testDeviceTwo",
                                "port": "6000",
                                "username": "testUsername",
                                'app': {"name": "HelloWorld"}
                                }

        filename = 'testappdevices.json'
        filepath = os.path.join(tests.config.test_data_path, filename)
        data = {'filename': filepath}
        self.post_with_status_check('/api/devices/export',
                                    data=json.dumps(data), headers=self.headers, content_type="application/json")

        with server.running_context.flask_app.app_context():
            server.running_context.Device.query.filter_by(name="testDevice").delete()
            server.running_context.Device.query.filter_by(name="testDeviceTwo").delete()
            server.database.db.session.commit()

        self.get_with_status_check('/api/devices/import',
                                   data=json.dumps(data), headers=self.headers, content_type="application/json")

        def convert_all_json_to_str(json_in):
            return {str(key): (str(value) if not isinstance(value, dict) else convert_all_json_to_str(value))
                    for key, value in json_in.items()}

        with server.running_context.flask_app.app_context():
            app = server.running_context.App.query.filter_by(name="HelloWorld").all()
            devices = server.running_context.Device.query.all()
            self.assertEqual(len(app), 1)
            app = app[0]
            self.assertEqual(len(app.devices), 2)
            checked_apps = 0
            for device in devices:
                if device.name == 'testDevice':
                    device_json = convert_all_json_to_str(device.as_json())
                    if 'id' in device_json:
                        device_json.pop('id', None)
                    self.assertIn('app', device_json)
                    device_json['app'].pop('id', None)
                    self.assertDictEqual(device_json, test_device_one_json)
                    checked_apps += 1
                elif device.name == 'testDeviceTwo':
                    device_json = convert_all_json_to_str(device.as_json())
                    if 'id' in device_json:
                        device_json.pop('id', None)
                    self.assertIn('app', device_json)
                    device_json['app'].pop('id', None)
                    self.assertDictEqual(device_json, test_device_two_json)
                    checked_apps += 1
            self.assertEqual(checked_apps, 2)

    def test_device_password(self):
        data = {"name": self.name, "username": self.username, "password": self.password, "ip": self.ip, "port": self.port,
                "extraFields": json.dumps(self.extraFields), "app": "HelloWorld"}
        self.put_with_status_check('/api/devices'.format(self.name),
                                   data=json.dumps(data),
                                   headers=self.headers,
                                   status_code=OBJECT_CREATED,
                                   content_type="application/json")

        with server.running_context.flask_app.app_context():
            device = server.running_context.Device.query.filter_by(name=self.name).first()

            try:
                with open(core.config.paths.AES_key_path, 'rb') as key_file:
                    key = key_file.read()
            except (OSError, IOError) as e:
                print(e)

            pw = ''
            if key:
                aes = pyaes.AESModeOfOperationCTR(key)
                pw = aes.decrypt(device.password)

            self.assertEqual(self.password, pw.decode("utf-8"))
