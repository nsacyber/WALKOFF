import unittest
from datetime import datetime, timedelta

import walkoff.server.flaskserver
from tests.util import execution_db_help
from walkoff.helpers import timestamp_to_datetime
from walkoff.serverdb import db, User, Role, add_user, remove_user


class TestUserRolesDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = walkoff.server.flaskserver.app.test_request_context()
        cls.context.push()
        db.create_all()

        execution_db_help.setup_dbs()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()

    def tearDown(self):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin' and role.name != 'guest']:
            db.session.delete(role)
        db.session.commit()

    def assertUserRolesEqual(self, user, roles):
        self.assertSetEqual({role.id for role in user.roles}, roles)

    def assertLoginCount(self, user, login_count):
        self.assertEqual(user.login_count, login_count)

    def assertUserTimestamps(self, user, current_login=None, last_login=None, delta=timedelta(milliseconds=100)):
        if current_login is None:
            self.assertIsNone(user.current_login_at)
        else:
            self.assertAlmostEqual(user.current_login_at, current_login, delta=delta)
        if last_login is None:
            self.assertIsNone(user.last_login_at)
        else:
            self.assertAlmostEqual(user.last_login_at, last_login, delta=delta)

    def assertUserIps(self, user, current_ip=None, last_ip=None):
        if current_ip is None:
            self.assertIsNone(user.current_login_ip)
        else:
            self.assertEqual(user.current_login_ip, current_ip)
        if last_ip is None:
            self.assertIsNone(user.last_login_ip)
        else:
            self.assertEqual(user.last_login_ip, last_ip)

    def test_user_init(self):
        user = User('username', 'password')
        self.assertEqual(user.username, 'username')
        self.assertUserRolesEqual(user, set())
        self.assertUserTimestamps(user)
        self.assertUserIps(user)
        db.session.add(user)
        db.session.commit()
        self.assertLoginCount(user, 0)

    def test_verify_valid_password(self):
        user = User('username', 'password')
        self.assertTrue(user.verify_password('password'))

    def test_password_stored_encrypted(self):
        user = User('username', 'password')
        self.assertNotEqual(user.password, 'password')

    def test_verify_invalid_password(self):
        user = User('username', 'invalid')
        self.assertFalse(user.verify_password('password'))

    def test_first_login(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user.login('192.168.0.1')
        self.assertUserTimestamps(user, current_login=datetime.utcnow())
        self.assertUserIps(user, current_ip='192.168.0.1')
        self.assertLoginCount(user, 1)

    def test_second_login(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user.login('192.168.0.1')
        first_login_timestamp = datetime.utcnow()
        user.login('192.168.0.2')
        self.assertUserTimestamps(user, current_login=datetime.utcnow(), last_login=first_login_timestamp)
        self.assertUserIps(user, current_ip='192.168.0.2', last_ip='192.168.0.1')
        self.assertLoginCount(user, 2)

    def test_logout_from_first_login(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user.login('192.168.0.1')
        user.logout()
        self.assertLoginCount(user, 0)

    def test_logout_from_second_login(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user.login('192.168.0.1')
        user.login('192.168.0.2')
        user.logout()
        self.assertLoginCount(user, 1)

    def test_too_many_logouts(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user.login('192.168.0.1')
        user.logout()
        user.logout()
        self.assertLoginCount(user, 0)

    @staticmethod
    def add_roles_to_db(num_roles):
        role_names = {'role{}'.format(i) for i in range(1, num_roles + 1)}
        role_ids = []
        roles = [Role(name=name) for name in role_names]
        for role in roles:
            db.session.add(role)
        db.session.commit()
        for role in roles:
            role_ids.append(role.id)
        return role_ids

    def test_set_roles_none_in_user_none_in_db(self):
        user = User('username', 'password')
        user.set_roles([10, 20, 30])
        self.assertUserRolesEqual(user, set())

    def test_set_roles_to_none_with_none_in_user(self):
        user = User('username', 'password')
        user.set_roles([])
        self.assertUserRolesEqual(user, set())

    def test_set_roles_to_none_with_some_in_user(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles(role_ids)
        db.session.commit()
        user.set_roles([])
        db.session.commit()
        self.assertUserRolesEqual(user, set())

    def test_set_roles_none_in_user_all_in_db(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles(role_ids)
        self.assertUserRolesEqual(user, set(role_ids))

    def test_set_roles_none_in_user_some_in_db(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        added_roles = set(role_ids)
        added_roles.add(30)
        user.set_roles(added_roles)
        db.session.commit()
        self.assertUserRolesEqual(user, set(role_ids))

    def test_set_roles_some_in_user_none_in_db(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        x = role_ids.pop()
        user = User('username', 'password')
        user.set_roles(role_ids)
        user.set_roles({x + 1, x + 2, x + 3})
        self.assertUserRolesEqual(user, set())

    def test_set_roles_some_in_user_all_in_db(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        x = role_ids.pop()
        user = User('username', 'password')
        user.set_roles(role_ids)
        user.set_roles({x - 1, x})
        self.assertUserRolesEqual(user, {x - 1, x})

    def test_set_roles_some_in_user_some_in_db(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        x = role_ids.pop()
        user = User('username', 'password')
        user.set_roles(role_ids)
        user.set_roles({x - 1, x, x + 1})
        db.session.commit()
        self.assertUserRolesEqual(user, {x - 1, x})

    def test_has_role_user_with_no_roles(self):
        user = User('username', 'password')
        self.assertFalse(user.has_role(100))

    def test_has_role_user_with_role(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles(role_ids)
        db.session.commit()
        for role in role_ids:
            self.assertTrue(user.has_role(role))

    def test_has_role_user_without_role(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles(role_ids)
        self.assertFalse(user.has_role('invalid'))

    def test_add_user(self):
        user = add_user('username', 'password')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'username')
        self.assertIsNotNone(User.query.filter_by(username='username').first())

    def test_add_user_already_exists(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user = add_user('username', 'password')
        self.assertIsNone(user)

    def test_remove_user(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        remove_user('username')
        self.assertIsNone(User.query.filter_by(username='username').first())

    def test_remove_user_not_found(self):
        remove_user('username')
        self.assertIsNone(User.query.filter_by(username='username').first())

    def test_as_json(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        db.session.add(user)
        user.set_roles(role_ids)
        user.login('192.168.0.1')
        user.login('192.168.0.2')
        user_json = user.as_json()
        expected = {"id": 1,
                    "username": 'username',
                    "active": True,
                    "roles": [{'name': role, 'description': '', 'resources': []} for role in
                              ['role1', 'role2', 'role3']]}
        self.assertSetEqual(set(user_json.keys()), set(expected.keys()))
        self.assertEqual(user_json['username'], 'username')
        self.assertEqual(user_json['active'], True)
        for role in user_json['roles']:
            self.assertIn('id', role)
            self.assertIn(role['name'], ['role1', 'role2', 'role3'])
            self.assertListEqual(role['resources'], [])
            self.assertEqual(role['description'], '')

    def test_as_json_with_user_history(self):
        role_ids = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        db.session.add(user)
        user.set_roles(role_ids)
        user.login('192.168.0.1')
        first_login_timestamp = datetime.utcnow()
        user.login('192.168.0.2')
        second_login_timestamp = datetime.utcnow()
        user_json = user.as_json(with_user_history=True)
        expected = {"id": 1,
                    "username": 'username',
                    "roles": [{'name': role, 'description': '', 'resources': []} for role in
                              ['role1', 'role2', 'role3']],
                    "active": True,
                    "last_login_at": first_login_timestamp,
                    "current_login_at": second_login_timestamp,
                    "last_login_ip": '192.168.0.1',
                    "current_login_ip": '192.168.0.2',
                    "login_count": 2}
        self.assertSetEqual(set(user_json.keys()), set(expected.keys()))
        for key in ['username', 'active', 'last_login_ip', 'current_login_ip', 'login_count']:
            self.assertEqual(user_json[key], expected[key], '{} for user\'s json in incorrect'.format(key))

        self.assertAlmostEqual(timestamp_to_datetime(user_json['last_login_at']), first_login_timestamp,
                               delta=timedelta(milliseconds=100))
        self.assertAlmostEqual(timestamp_to_datetime(user_json['current_login_at']), second_login_timestamp,
                               delta=timedelta(milliseconds=100))
        for role in user_json['roles']:
            self.assertIn('id', role)
            self.assertIn(role['name'], ['role1', 'role2', 'role3'])
            self.assertListEqual(role['resources'], [])
            self.assertEqual(role['description'], '')

    def test_roles_as_json_with_users_one_user(self):
        role = Role('role1')
        db.session.add(role)
        db.session.commit()
        user = User('username', 'password')
        db.session.add(user)
        user.set_roles([role.id])
        expected = {'name': 'role1', 'description': '', 'resources': [], 'users': ['username']}
        role_json = role.as_json(with_users=True)
        role_json.pop('id')
        self.assertDictEqual(role_json, expected)

    def test_roles_as_json_with_users_multiple_users(self):
        role = Role('role1')
        db.session.add(role)
        db.session.commit()
        user = User('username', 'password')
        user2 = User('user2', 'thisisagreatpassword')
        db.session.add(user)
        db.session.add(user2)
        user.set_roles([role.id])
        user2.set_roles([role.id])
        expected = {'name': 'role1', 'description': '', 'resources': [], 'users': ['username', 'user2']}
        role_json = role.as_json(with_users=True)
        role_json.pop('id')
        self.assertDictEqual(role_json, expected)
