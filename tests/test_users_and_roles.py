import json

from flask_security.utils import verify_password
from server import flaskserver as server
from tests.util.servertestcase import ServerTestCase


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
        self.put_with_status_check('/roles/'+self.name, 'role added {0}'.format(self.name), data=data, headers=self.headers)
        self.put_with_status_check('/roles/'+self.name, 'role exists', data=data, headers=self.headers)

    def test_display_all_roles(self):
        data = {"name": self.name}
        self.app.put('/roles/'+self.name, data=data, headers=self.headers).get_data(as_text=True)

        response = json.loads(self.app.get('/roles', headers=self.headers).get_data(as_text=True))
        self.assertEqual(response, ["admin", self.name])

    def test_edit_role_description(self):
        data = {"name": self.name}
        json.loads(self.app.put('/roles/'+self.name, data=data, headers=self.headers).get_data(as_text=True))

        data = {"name": self.name, "description": self.description}
        response = json.loads(
            self.app.post('/roles/'+self.name, data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["name"], self.name)
        self.assertEqual(response["description"], self.description)

    def test_add_user(self):
        data = {"username": self.email, "password": self.password}
        response = json.loads(self.app.put('/users/'+self.email, data=data, headers=self.headers).get_data(as_text=True))
        self.assertTrue("user added" in response["status"])

        self.put_with_status_check('/users/'+self.email, 'user exists', data=data, headers=self.headers)

    def test_edit_user_password(self):
        data = {"username": self.email, "password": self.password}
        json.loads(self.app.put('/users/'+self.email, data=data, headers=self.headers).get_data(as_text=True))

        data = {"password": self.password}
        response = json.loads(
            self.app.post('/users/' + self.email, data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["username"], self.email)

        data = {"password": "testPassword"}
        self.app.post('/users/' + self.email, data=data, headers=self.headers).get_data(as_text=True)
        with server.app.app_context():
            user = server.database.user_datastore.get_user(self.email)
            self.assertTrue(verify_password("testPassword", user.password))

    def test_remove_user(self):
        data = {"username": self.email, "password": self.password}
        json.loads(self.app.put('/users/'+self.email, data=data, headers=self.headers).get_data(as_text=True))

        self.delete_with_status_check('/users/{0}'.format(self.email), 'user removed', headers=self.headers)

    def test_add_role_to_user(self):
        data = {"username": self.email, "password": self.password}
        json.loads(self.app.put('/users/'+self.email, data=data, headers=self.headers).get_data(as_text=True))

        data = {"name": self.name}
        self.put_with_status_check('/roles/'+self.name, "role added {0}".format(self.name), data=data, headers=self.headers)

        data = {"role-0": "admin", "role-1": self.name}
        response = json.loads(self.app.post('/users/' + self.email,
                                            data=data, headers=self.headers).get_data(as_text=True))
        roles = [self.name, "admin"]
        self.assertEqual(len(roles), len(response["roles"]))
        self.assertEqual(response["roles"][0]["name"], "admin")
        self.assertEqual(response["roles"][1]["name"], self.name)

    def test_add_user(self):
        data = {"username": self.email, "password": self.password}
        response = json.loads(self.app.put('/users/'+self.email, data=data, headers=self.headers).get_data(as_text=True))
        self.assertTrue("user added" in response["status"])

        data = {"username": "test", "password": self.password}
        response = json.loads(
            self.app.put('/users/' + "test", data=data, headers=self.headers).get_data(as_text=True))
        self.assertTrue("user added" in response["status"])

        response = self.app.get('/users').get_data(as_text=True)
        self.assertIn(self.email, response)
        self.assertIn("test", response)
