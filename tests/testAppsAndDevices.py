import json
import unittest

from server import database
from server import appDevice
from server import flaskServer as server


class TestAppsAndDevices(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'), follow_redirects=True).get_data(
            as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}
        self.name = "testDevice"

        self.username = "testUsername"
        self.password = "testPassword"
        self.ip = "127.0.0.1"
        self.port = 6000

        self.extraFields = {"extraFieldOne": "extraNameOne", "extraFieldTwo": "extraNameTwo"}

    def tearDown(self):
        appDevice.Device.query.filter_by(name=self.name).delete()
        appDevice.Device.query.filter_by(name="testDeviceTwo").delete()
        database.db.session.commit()

    def testAddDevice(self):
        data = {"name": self.name, "username": self.username, "pw": self.password, "ipaddr": self.ip, "port": self.port,
                "extraFields": json.dumps(self.extraFields)}
        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/add', data=data, headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device successfully added")

        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/add', data=data, headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device could not be added")

    def testDisplayDevice(self):
        data = {"name": self.name, "username": self.username, "pw": self.password, "ipaddr": self.ip, "port": self.port,
                "extraFields": str(self.extraFields)}
        json.loads(
            self.app.post('/configuration/HelloWorld/devices/add', data=data, headers=self.headers).get_data(
                as_text=True))

        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/testDevice/display', headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["username"], self.username)
        self.assertEqual(response["name"], self.name)
        self.assertEqual(response["ip"], self.ip)
        self.assertEqual(response["port"], str(self.port))
        self.assertEqual(response["extraFieldOne"], "extraNameOne")
        self.assertEqual(response["extraFieldTwo"], "extraNameTwo")

    def testEditDevice(self):
        data = {"name": self.name, "username": self.username, "pw": self.password, "ipaddr": self.ip, "port": self.port,
                "extraFields": str(self.extraFields)}
        json.loads(
            self.app.post('/configuration/HelloWorld/devices/add', data=data, headers=self.headers).get_data(
                as_text=True))

        data = {"ipaddr": "192.168.196.1"}
        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/testDevice/edit', data=data,
                          headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device successfully edited")

        data = {"port": 6001}
        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/testDevice/edit', data=data,
                          headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device successfully edited")

        data = {"extraFields": json.dumps({"extraFieldOne": "extraNameOneOne"})}
        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/testDevice/edit', data=data,
                          headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device successfully edited")

        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/testDevice/display', headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["extraFieldOne"], "extraNameOneOne")

    def testAddAndDisplayMultipleDevices(self):
        data = {"name": self.name, "username": self.username, "pw": self.password, "ipaddr": self.ip, "port": self.port,
                "extraFields": json.dumps(self.extraFields)}
        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/add', data=data, headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device successfully added")
        data = {"name": "testDeviceTwo", "username": self.username, "pw": self.password, "ipaddr": self.ip,
                "port": self.port,
                "extraFields": json.dumps(self.extraFields)}
        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/add', data=data, headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device successfully added")
        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/all', headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]["name"], self.name)
        self.assertEqual(response[1]["name"], "testDeviceTwo")
        self.assertEqual(response[0]["app"]["name"], response[1]["app"]["name"])
