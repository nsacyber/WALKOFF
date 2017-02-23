import json
import unittest

from server import database
from server import flaskServer as server


class TestUsersAndRoles(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'), follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token" : self.key}
        self.name = "testRoleOne"
        self.description = "testRoleOne description"

        self.email = "testUser"
        self.password = "password"

    def tearDown(self):
        database.Role.query.filter_by(name=self.name).delete()
        database.db.session.commit()

        database.User.query.filter_by(email=self.email).delete()
        database.db.session.commit()

    def testAddRole(self):
        data = {"name" : self.name}
        response = json.loads(self.app.post('/roles/add', data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], "role added {0}".format(self.name))

        response = json.loads(self.app.post('/roles/add', data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], "role exists")

    def testEditRoleDescr(self):
        data = {"name": self.name}
        json.loads(self.app.post('/roles/add', data=data, headers=self.headers).get_data(as_text=True))

        data = {"name" : self.name, "description" : self.description}
        response = json.loads(self.app.post('/roles/edit/'+self.name, data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["name"], self.name)
        self.assertEqual(response["description"], self.description)

    def testAddUser(self):
        data = {"username": self.email, "password":self.password}
        response = json.loads(self.app.post('/users/add', data=data, headers=self.headers).get_data(as_text=True))
        self.assertTrue("user added" in response["status"])

        response = json.loads(self.app.post('/users/add', data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], "user exists")

    def testEditUser(self):
        data = {"username": self.email, "password": self.password}
        json.loads(self.app.post('/users/add', data=data, headers=self.headers).get_data(as_text=True))

        data = {"password": self.password}
        response = json.loads(self.app.post('/users/'+self.email+'/edit', data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["username"], self.email)

    def testRemoveUser(self):
        data = {"username": self.email, "password": self.password}
        json.loads(self.app.post('/users/add', data=data, headers=self.headers).get_data(as_text=True))

        response = json.loads(self.app.post('/users/'+self.email+'/remove', headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], "user removed")