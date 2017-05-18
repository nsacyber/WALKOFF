import json

from flask_security.utils import verify_password
from server import flaskserver as server
from tests.util.servertestcase import ServerTestCase
from server.return_codes import *


class TestUsersAndRoles(ServerTestCase):
    def setUp(self):
        self.name = "testRoleOne"
        self.description = "testRoleOne description"

        self.email = "testUser"
        self.password = "password"

    def tearDown(self):
        with server.running_context.flask_app.app_context():
            # server.running_context.User.query.filter_by(email=self.email).delete()
            # server.database.db.session.commit()

            email = self.email
            u = server.running_context.user_datastore.get_user(email)
            if u:
                server.running_context.user_datastore.delete_user(u)

            testu = server.running_context.user_datastore.get_user("test")
            if testu:
                server.running_context.user_datastore.delete_user(testu)

            server.running_context.Role.query.filter_by(name=self.name).delete()
            server.database.db.session.commit()

    def test_add_role(self):
        data = {"name": self.name}
        self.put_with_status_check('/roles/'+self.name, data=data, headers=self.headers, status_code=OBJECT_CREATED)
        self.put_with_status_check('/roles/'+self.name, error='Role already exists.', data=data, headers=self.headers,
                                   status_code=OBJECT_EXISTS_ERROR)

    def test_display_all_roles(self):
        data = {"name": self.name}
        self.put_with_status_check('/roles/'+self.name, data=data, headers=self.headers, status_code=OBJECT_CREATED)

        response = json.loads(self.app.get('/roles', headers=self.headers).get_data(as_text=True))
        self.assertEqual(response, ["admin", self.name])

    def test_edit_role_description(self):
        data = {"name": self.name}
        self.put_with_status_check('/roles/'+self.name, data=data, headers=self.headers, status_code=OBJECT_CREATED)

        data = {"name": self.name, "description": self.description}
        response = json.loads(
            self.app.post('/roles/'+self.name, data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["name"], self.name)
        self.assertEqual(response["description"], self.description)

    def test_add_user(self):
        data = {"username": self.email, "password": self.password}
        self.put_with_status_check('/users/'+self.email, data=data, headers=self.headers, status_code=OBJECT_CREATED)

        self.put_with_status_check('/users/'+self.email, error='User already exists.', data=data, headers=self.headers,
                                   status_code=OBJECT_EXISTS_ERROR)

    def test_edit_user_password(self):
        data = {"username": self.email, "password": self.password}
        self.put_with_status_check('/users/'+self.email, data=data, headers=self.headers, status_code=OBJECT_CREATED)

        data = {"password": self.password}
        response = json.loads(
            self.app.post('/users/' + self.email, data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["username"], self.email)

        data = {"password": "testPassword"}
        self.app.post('/users/' + self.email, data=data, headers=self.headers)
        with server.app.app_context():
            user = server.database.user_datastore.get_user(self.email)
            self.assertTrue(verify_password("testPassword", user.password))

    def test_remove_user(self):
        data = {"username": self.email, "password": self.password}
        self.put_with_status_check('/users/'+self.email, data=data, headers=self.headers, status_code=OBJECT_CREATED)

        self.delete_with_status_check('/users/{0}'.format(self.email), status_code=SUCCESS, headers=self.headers)

    def test_add_role_to_user(self):
        data = {"username": self.email, "password": self.password}
        self.put_with_status_check('/users/'+self.email, data=data, headers=self.headers, status_code=OBJECT_CREATED)

        data = {"name": self.name}
        self.put_with_status_check('/roles/'+self.name, data=data, headers=self.headers, status_code=OBJECT_CREATED)

        data = {"role-0": "admin", "role-1": self.name}
        response = json.loads(self.app.post('/users/' + self.email,
                                            data=data, headers=self.headers).get_data(as_text=True))
        roles = [self.name, "admin"]
        self.assertEqual(len(roles), len(response["roles"]))
        self.assertEqual(response["roles"][0]["name"], "admin")
        self.assertEqual(response["roles"][1]["name"], self.name)

    def test_add_user(self):
        data = {"username": self.email, "password": self.password}
        self.put_with_status_check('/users/'+self.email, data=data, headers=self.headers, status_code=OBJECT_CREATED)

        data = {"username": "test", "password": self.password}
        self.put_with_status_check('/users/' + "test", data=data, headers=self.headers, status_code=OBJECT_CREATED)

        response = self.app.get('/users').get_data(as_text=True)
        self.assertIn(self.email, response)
        self.assertIn("test", response)
