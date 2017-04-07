import json
import unittest

from flask_security.utils import verify_password
from server import flaskServer as server
from tests.util.assertwrappers import post_with_status_check


class TestUsersAndRoles(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'), follow_redirects=True).get_data(
            as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}
        self.name = "testRoleOne"
        self.description = "testRoleOne description"

        self.email = "testUser"
        self.password = "password"

    def tearDown(self):
        with server.running_context.flask_app.app_context():
            # server.running_context.User.query.filter_by(email=self.email).delete()
            # server.database.db.session.commit()

            email = self.email
            u = server.user_datastore.get_user(email)
            if u:
                server.user_datastore.delete_user(u)

            server.running_context.Role.query.filter_by(name=self.name).delete()
            server.database.db.session.commit()

    def test_add_role(self):
        data = {"name": self.name}
        post_with_status_check(self, self.app, '/roles/add', 'role added {0}'.format(self.name),
                               data=data, headers=self.headers)
        post_with_status_check(self, self.app, '/roles/add', 'role exists', data=data, headers=self.headers)

    def test_display_all_roles(self):
        data = {"name": self.name}
        self.app.post('/roles/add', data=data, headers=self.headers).get_data(as_text=True)

        response = json.loads(self.app.get('/roles', headers=self.headers).get_data(as_text=True))
        self.assertEqual(response, ["admin", self.name])

    def test_edit_role_description(self):
        data = {"name": self.name}
        json.loads(self.app.post('/roles/add', data=data, headers=self.headers).get_data(as_text=True))

        data = {"name": self.name, "description": self.description}
        response = json.loads(
            self.app.post('/roles/edit/' + self.name, data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["name"], self.name)
        self.assertEqual(response["description"], self.description)

    def test_add_user(self):
        data = {"username": self.email, "password": self.password}
        response = json.loads(self.app.post('/users/add', data=data, headers=self.headers).get_data(as_text=True))
        self.assertTrue("user added" in response["status"])

        post_with_status_check(self, self.app, '/users/add', 'user exists', data=data, headers=self.headers)

    def test_edit_user_password(self):
        data = {"username": self.email, "password": self.password}
        json.loads(self.app.post('/users/add', data=data, headers=self.headers).get_data(as_text=True))

        data = {"password": self.password}
        response = json.loads(
            self.app.post('/users/' + self.email + '/edit', data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["username"], self.email)

        data = {"password": "testPassword"}
        self.app.post('/users/' + self.email + '/edit', data=data, headers=self.headers).get_data(as_text=True)
        with server.app.app_context():
            user = server.database.user_datastore.get_user(self.email)
            self.assertTrue(verify_password("testPassword", user.password))

    def test_remove_user(self):
        data = {"username": self.email, "password": self.password}
        json.loads(self.app.post('/users/add', data=data, headers=self.headers).get_data(as_text=True))

        post_with_status_check(self, self.app, '/users/{0}/remove'.format(self.email), 'user removed',
                               headers=self.headers)

    def test_add_role_to_user(self):
        data = {"username": self.email, "password": self.password}
        json.loads(self.app.post('/users/add', data=data, headers=self.headers).get_data(as_text=True))

        data = {"name": self.name}
        post_with_status_check(self, self.app, '/roles/add', "role added {0}".format(self.name), data=data,
                               headers=self.headers)

        data = {"role-0": "admin", "role-1": self.name}
        response = json.loads(self.app.post('/users/' + self.email + '/edit',
                                            data=data, headers=self.headers).get_data(as_text=True))
        roles = [self.name, "admin"]
        self.assertEqual(len(roles), len(response["roles"]))
        self.assertEqual(response["roles"][0]["name"], "admin")
        self.assertEqual(response["roles"][1]["name"], self.name)
