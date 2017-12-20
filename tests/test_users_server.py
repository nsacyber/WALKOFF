import json

from server.extensions import db
from server.database.user import User
from server.database.role import Role
from server.database import add_user
from server.returncodes import *
from tests.util.servertestcase import ServerTestCase


class TestUserServer(ServerTestCase):
    def tearDown(self):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin' and role.name != 'guest']:
            db.session.delete(role)
        db.session.commit()

    def assertUserCreatedResponse(self, username, response):
        user = User.query.filter_by(username=username).first()
        self.assertIsNotNone(user)
        self.assertEqual(response, user.as_json())

    def setup_guest_user(self):
        user = add_user('guest', 'guest', ['guest'])
        db.session.add(user)
        db.session.commit()
        return user

    def test_read_users(self):
        user = User('username', 'asdfghjkl;')
        db.session.add(user)
        db.session.commit()
        response = self.get_with_status_check('/api/users', headers=self.headers, status_code=SUCCESS)
        self.assertSetEqual({user['username'] for user in response}, {'admin', 'username'})

    def test_create_user_name_password_only(self):
        data = {'username': 'test_user', 'password': 'NoH4x0rzPls!'}
        response = self.put_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                              data=json.dumps(data), status_code=OBJECT_CREATED)
        self.assertUserCreatedResponse('test_user', response)

    def test_create_user_username_already_exists(self):
        user = User('username', 'asdfghjkl;')
        db.session.add(user)
        db.session.commit()
        data = {'username': 'username', 'password': 'NoH4x0rzPls!'}
        self.put_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                   data=json.dumps(data), status_code=OBJECT_EXISTS_ERROR)

    # TODO: Fix.
    def test_create_user_with_roles(self):
        role = Role('role1')
        db.session.add(role)
        db.session.commit()
        data = {'username': 'username', 'password': 'NoH4x0rzPls!', 'roles': [role.id]}
        response = self.put_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                              data=json.dumps(data), status_code=OBJECT_CREATED)
        self.assertUserCreatedResponse('username', response)

    def test_read_user(self):
        user = User('username', 'asdfghjkl;')
        db.session.add(user)
        db.session.commit()
        response = self.get_with_status_check('/api/users/{}'.format(user.id), headers=self.headers,
                                              status_code=SUCCESS)
        self.assertDictEqual(response, user.as_json())

    def test_read_user_user_does_not_exist(self):
        self.get_with_status_check('/api/users/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_update_user_password_only(self):
        user = User('username', 'asdfghjkl;')
        db.session.add(user)
        db.session.commit()
        data = {'id': user.id, 'old_password': 'asdfghjkl;', 'password': 'changed!'}
        response = self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                               data=json.dumps(data), status_code=SUCCESS)
        self.assertDictEqual(response, user.as_json())
        self.assertTrue(user.verify_password('changed!'))

    def test_update_user_password_only_invalid_old_password(self):
        user = User('username', 'asdfghjkl;')
        db.session.add(user)
        db.session.commit()
        data = {'id': user.id, 'old_password': 'incorrectpassword', 'password': 'changed!'}
        self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                    data=json.dumps(data), status_code=BAD_REQUEST)
        self.assertTrue(user.verify_password('asdfghjkl;'))

    # TODO: Fix.
    def test_update_user_with_roles(self):
        role = Role('role1')
        db.session.add(role)
        db.session.commit()
        user = User('username', 'supersecretshhhhh')
        db.session.add(user)
        db.session.commit()
        data = {'id': user.id, 'roles': [role.id]}
        response = self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                               data=json.dumps(data), status_code=SUCCESS)
        self.assertDictEqual(response, user.as_json())
        self.assertSetEqual({role.name for role in user.roles}, {'role1'})

    def test_update_username(self):
        user = User('username', 'whisperDieselEngine')
        db.session.add(user)
        db.session.commit()
        data = {'id': user.id, 'username': 'new_name'}
        response = self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                               data=json.dumps(data), status_code=SUCCESS)
        self.assertEqual(user.username, 'new_name')
        self.assertDictEqual(response, user.as_json())

    def test_update_username_name_already_exists(self):
        user = User('username', 'whisperDieselEngine')
        db.session.add(user)
        user2 = User('user2', 'shhnow')
        db.session.add(user)
        db.session.add(user2)
        db.session.commit()
        data = {'id': user.id, 'username': 'user2'}
        self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                    data=json.dumps(data), status_code=BAD_REQUEST)
        self.assertTrue(user.verify_password('whisperDieselEngine'))  # check password wasn't changed

    def test_change_password_and_username(self):
        user = User('username', 'asdfghjkl;')
        db.session.add(user)
        db.session.commit()
        data = {'id': user.id, 'old_password': 'asdfghjkl;', 'password': 'changed!', 'username': 'new_name'}
        response = self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                               data=json.dumps(data), status_code=SUCCESS)
        self.assertTrue(user.verify_password('changed!'))
        self.assertEqual(user.username, 'new_name')
        self.assertDictEqual(response, user.as_json())

    def test_change_password_and_username_invalid_username(self):
        user = User('username', 'whisperDieselEngine')
        db.session.add(user)
        user2 = User('user2', 'somethingelse#@!@#')
        db.session.add(user)
        db.session.add(user2)
        db.session.commit()
        data = {'id': user.id, 'old_password': 'asdfghjkl;', 'password': 'changed!', 'username': 'user2'}
        self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                    data=json.dumps(data), status_code=BAD_REQUEST)
        self.assertTrue(user.verify_password('whisperDieselEngine'))
        self.assertEqual(user.username, 'username')
        self.assertTrue(user2.verify_password('somethingelse#@!@#'))
        self.assertEqual(user2.username, 'user2')

    def test_change_password_and_username_invalid_password(self):
        user = User('username', 'whisperDieselEngine')
        db.session.add(user)
        db.session.commit()
        data = {'id': user.id, 'old_password': 'invalid', 'password': 'changed!', 'username': 'new_name'}
        self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                    data=json.dumps(data), status_code=BAD_REQUEST)
        self.assertTrue(user.verify_password('whisperDieselEngine'))
        self.assertEqual(user.username, 'username')

    def test_update_active_with_guest_user(self):
        user = self.setup_guest_user()
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='guest', password='guest')))
        key = json.loads(response.get_data(as_text=True))
        access_token = key['access_token']
        headers = {'Authorization': 'Bearer {}'.format(access_token)}
        data = {'id': user.id, 'active': False}
        self.post_with_status_check('/api/users', headers=headers, content_type='application/json',
                                    data=json.dumps(data), status_code=SUCCESS)
        self.assertTrue(user.active)

    def test_update_active_with_admin_user(self):
        user = self.setup_guest_user()
        data = {'id': user.id, 'active': False}
        self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                    data=json.dumps(data), status_code=SUCCESS)
        self.assertFalse(user.active)

    def test_update_different_user_not_admin(self):
        self.setup_guest_user()
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='guest', password='guest')))
        key = json.loads(response.get_data(as_text=True))
        access_token = key['access_token']
        headers = {'Authorization': 'Bearer {}'.format(access_token)}
        admin = User.query.filter_by(username='admin').first()
        data = {'id': admin.id, 'username': 'somethingelse'}
        self.post_with_status_check('/api/users', headers=headers, content_type='application/json',
                                    data=json.dumps(data), status_code=FORBIDDEN_ERROR)

    def test_update_user_invalid_id(self):
        data = {'id': 404, 'username': 'new_name'}
        self.post_with_status_check('/api/users', headers=self.headers, content_type='application/json',
                                    data=json.dumps(data), status_code=OBJECT_DNE_ERROR)

    def test_delete_user(self):
        user = User('username', 'asdfghjkl;')
        db.session.add(user)
        db.session.commit()
        self.delete_with_status_check('/api/users/{}'.format(user.id), headers=self.headers, status_code=SUCCESS)

    def test_delete_user_invalid_id(self):
        self.delete_with_status_check('/api/users/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_delete_current_user(self):
        user = add_user('test', 'test')
        user.set_roles({'admin'})
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='test', password='test')))
        key = json.loads(response.get_data(as_text=True))
        access_token = key['access_token']
        headers = {'Authorization': 'Bearer {}'.format(access_token)}
        self.delete_with_status_check('/api/users/{}'.format(user.id), headers=headers, status_code=FORBIDDEN_ERROR)
