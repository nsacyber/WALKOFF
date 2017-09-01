import json

from flask_security.utils import verify_password
from server import flaskserver as server
from tests.util.servertestcase import ServerTestCase
from server.returncodes import *


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
            user = server.running_context.user_datastore.get_user(email)
            if user:
                server.running_context.user_datastore.delete_user(user)

            test_user = server.running_context.user_datastore.get_user("test")
            if test_user:
                server.running_context.user_datastore.delete_user(test_user)

            server.running_context.Role.query.filter_by(name=self.name).delete()
            server.database.db.session.commit()

    def test_add_role(self):
        data = {"name": self.name}
        self.put_with_status_check('/api/roles', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type='application/json')

    def test_add_role_already_exists(self):
        data = {"name": self.name}
        self.app.put('/api/roles', data=json.dumps(data), headers=self.headers, content_type='application/json')
        self.put_with_status_check('/api/roles', error='Role already exists.', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_EXISTS_ERROR, content_type='application/json')

    def test_display_all_roles(self):
        data = {"name": self.name}
        self.app.put('/api/roles', data=json.dumps(data), headers=self.headers, content_type='application/json')

        response = self.get_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS)
        self.assertEqual([role['name'] for role in response], ["admin", self.name])

    def test_edit_role_description(self):
        data = {"name": self.name}
        self.app.put('/api/roles', data=json.dumps(data), headers=self.headers, content_type='application/json')

        data = {"name": self.name, "description": self.description}
        response = self.post_with_status_check('/api/roles', data=json.dumps(data), headers=self.headers,
                                               status_code=SUCCESS, content_type='application/json')
        self.assertEqual(response["name"], self.name)
        self.assertEqual(response["description"], self.description)

    def test_add_user(self):
        data = {"username": self.email, "password": self.password}
        self.put_with_status_check('/api/users', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type='application/json')

    def test_add_user_already_exists(self):
        data = {"username": self.email, "password": self.password}
        self.app.put('/api/users', data=json.dumps(data), headers=self.headers, content_type='application/json')

        self.put_with_status_check('/api/users', data=json.dumps(data), headers=self.headers,
                                   status_code=OBJECT_EXISTS_ERROR, content_type='application/json')

    def test_edit_user_password(self):
        data = {"username": self.email, "password": self.password}
        response = json.loads(
            self.app.put('/api/users', data=json.dumps(data), headers=self.headers,
                         content_type='application/json').get_data(as_text=True))
        user_id = response['id']
        data = {"old_password": self.password, "password": "testPassword", "id": user_id}
        self.post_with_status_check('/api/users', data=json.dumps(data),
                                    headers=self.headers, content_type='application/json', status_code=SUCCESS)
        with server.app.app_context():
            user = server.database.user_datastore.get_user(self.email)
            self.assertTrue(verify_password("testPassword", user.password))

    def test_edit_user_password_does_not_match(self):
        data = {"username": self.email, "password": self.password}
        response = json.loads(
            self.app.put('/api/users', data=json.dumps(data), headers=self.headers,
                         content_type='application/json').get_data(as_text=True))
        user_id = response['id']
        data = {"old_password": 'supersecretpassword#1!', "password": "testPassword", "id": user_id}
        self.post_with_status_check('/api/users', data=json.dumps(data),
                                    headers=self.headers, content_type='application/json', status_code=400)
        with server.app.app_context():
            user = server.database.user_datastore.get_user(self.email)
            self.assertTrue(verify_password(self.password, user.password))

    def test_remove_user(self):
        data = {"username": self.email, "password": self.password}
        response = self.app.put('/api/users', data=json.dumps(data), headers=self.headers,
                     content_type='application/json').get_data(as_text=True)
        user_id = json.loads(response)['id']
        self.delete_with_status_check('/api/users/{0}'.format(user_id), status_code=SUCCESS, headers=self.headers)

    def test_add_role_to_user(self):
        data = {"username": self.email, "password": self.password}
        response = self.app.put('/api/users', data=json.dumps(data), headers=self.headers, content_type='application/json')
        user_id = json.loads(response.get_data(as_text=True))['id']
        data = {"name": self.name}
        self.app.put('/api/roles', data=json.dumps(data), headers=self.headers, content_type='application/json')

        data = {"roles": [{"name": "admin"}, {"name": self.name}], "id": user_id}
        response = self.post_with_status_check(
            '/api/users', data=json.dumps(data), headers=self.headers,
            status_code=SUCCESS, content_type='application/json')
        self.assertEqual(len(response["roles"]), 2)
        self.assertEqual(response["roles"][0]["name"], "admin")
        self.assertEqual(response["roles"][1]["name"], self.name)

    def test_get_all_users(self):
        data = {"username": self.email, "password": self.password}
        self.app.put('/api/users', data=json.dumps(data), headers=self.headers, content_type='application/json')

        data = {"username": "test", "password": self.password}
        self.app.put('/api/users', data=json.dumps(data), headers=self.headers, content_type='application/json')

        response = self.get_with_status_check('/api/users', headers=self.headers, status_code=SUCCESS)
        usernames = [user['username'] for user in response]
        self.assertIn(self.email, usernames)
        self.assertIn('test', usernames)
