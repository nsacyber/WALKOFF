import json
import unittest

from server import database
from server import appDevice
from server import flaskServer as server


class TestUsersAndRoles(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'), follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token" : self.key}
        self.name = "testDevice"

        self.username = "testUsername"
        self.password = "testPassword"
        self.ip = "127.0.0.1"
        self.port = 6000


    def tearDown(self):
        appDevice.Device.query.filter_by(name=self.name).delete()
        database.db.session.commit()

    def testAddDevice(self):
        data = {"name" : self.name, "username" : self.username, "pw" : self.password, "ipaddr" : self.ip, "port" : self.port}
        response = json.loads(self.app.post('/configuration/HelloWorld/devices/add', data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], "device successfully added")

        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/add', data=data, headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device could not be added")

    def testDisplayDevice(self):
        data = {"name": self.name, "username": self.username, "pw": self.password, "ipaddr": self.ip, "port": self.port}
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

    def testEditDevice(self):
        data = {"name": self.name, "username": self.username, "pw": self.password, "ipaddr": self.ip, "port": self.port}
        json.loads(
            self.app.post('/configuration/HelloWorld/devices/add', data=data, headers=self.headers).get_data(
                as_text=True))

        data = {"ipaddr" : "192.168.196.1"}
        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/testDevice/edit', data=data, headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device successfully edited")

        data = {"port": 6001}
        response = json.loads(
            self.app.post('/configuration/HelloWorld/devices/testDevice/edit', data=data,
                          headers=self.headers).get_data(
                as_text=True))
        self.assertEqual(response["status"], "device successfully edited")
