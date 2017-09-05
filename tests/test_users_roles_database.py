import unittest
from server.database import db, User, Role, add_user, remove_user
from datetime import datetime, timedelta
import server.flaskserver


class TestUserRolesDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.context = server.flaskserver.app.test_request_context()
        cls.context.push()
        db.create_all()

    def tearDown(self):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    def assertUserRolesEqual(self, user, roles):
        self.assertSetEqual({role.name for role in user.roles}, roles)

    def assertLoginCountAndActivity(self, user, login_count, active):
        self.assertEqual(user.login_count, login_count)
        if active:
            self.assertTrue(user.active)
        else:
            self.assertFalse(user.active)

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
        self.assertLoginCountAndActivity(user, 0, False)
        db.session.add(user)
        db.session.commit()

    def test_verify_valid_password(self):
        user = User('username', 'password')
        self.assertTrue(user.verify_password('password'))

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
        self.assertLoginCountAndActivity(user, 1, True)

    def test_second_login(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user.login('192.168.0.1')
        first_login_timestamp = datetime.utcnow()
        user.login('192.168.0.2')
        self.assertUserTimestamps(user, current_login=datetime.utcnow(), last_login=first_login_timestamp)
        self.assertUserIps(user, current_ip='192.168.0.2', last_ip='192.168.0.1')
        self.assertLoginCountAndActivity(user, 2, True)

    def test_logout_from_first_login(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user.login('192.168.0.1')
        user.logout()
        self.assertLoginCountAndActivity(user, 0, False)

    def test_logout_from_second_login(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user.login('192.168.0.1')
        user.login('192.168.0.2')
        user.logout()
        self.assertLoginCountAndActivity(user, 1, False)

    def test_too_many_logouts(self):
        user = User('username', 'password')
        db.session.add(user)
        db.session.commit()
        user.login('192.168.0.1')
        user.logout()
        user.logout()
        self.assertLoginCountAndActivity(user, 0, False)

    @staticmethod
    def add_roles_to_db(num_roles):
        role_names = {'role{}'.format(i) for i in range(1, num_roles + 1)}
        roles = [Role(name=name) for name in role_names]
        for role in roles:
            db.session.add(role)
        db.session.commit()
        return role_names

    def test_set_roles_none_in_user_none_in_db(self):
        user = User('username', 'password')
        user.set_roles(['role1', 'role2', 'role3'])
        self.assertUserRolesEqual(user, set())

    def test_set_roles_to_none_with_none_in_user(self):
        user = User('username', 'password')
        user.set_roles([])
        self.assertUserRolesEqual(user, set())

    def test_set_roles_to_none_with_some_in_user(self):
        role_names = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles(role_names)
        db.session.commit()
        user.set_roles([])
        db.session.commit()
        self.assertUserRolesEqual(user, set())

    def test_set_roles_none_in_user_all_in_db(self):
        role_names = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles(role_names)
        self.assertUserRolesEqual(user, role_names)

    def test_set_roles_none_in_user_some_in_db(self):
        role_names = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        added_roles = set(role_names)
        added_roles.add('role4')
        user.set_roles(added_roles)
        db.session.commit()
        self.assertUserRolesEqual(user, role_names)

    def test_set_roles_some_in_user_none_in_db(self):
        TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles({'role1', 'role2'})
        user.set_roles({'role4', 'role5', 'role6'})
        self.assertUserRolesEqual(user, set())

    def test_set_roles_some_in_user_all_in_db(self):
        TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles({'role1', 'role2'})
        user.set_roles({'role2', 'role3'})
        self.assertUserRolesEqual(user, {'role2', 'role3'})

    def test_set_roles_some_in_user_some_in_db(self):
        TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles({'role1', 'role2'})
        user.set_roles({'role2', 'role3', 'role4'})
        db.session.commit()
        self.assertUserRolesEqual(user, {'role2', 'role3'})

    def test_has_role_user_with_no_roles(self):
        user = User('username', 'password')
        self.assertFalse(user.has_role('role3'))

    def test_has_role_user_with_role(self):
        role_names = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles(role_names)
        db.session.commit()
        for role in role_names:
            self.assertTrue(user.has_role(role))

    def test_has_role_user_without_role(self):
        role_names = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        user.set_roles(role_names)
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
        role_names = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        db.session.add(user)
        user.set_roles(role_names)
        user.login('192.168.0.1')
        user.login('192.168.0.2')
        user_json = user.as_json()
        expected = {"id": 1,
                    "username": 'username',
                    "roles": [{'name': role, 'description': '', 'pages': []} for role in ['role1', 'role2', 'role3']]}
        self.assertSetEqual(set(user_json.keys()), set(expected.keys()))
        self.assertEqual(user_json['username'], 'username')
        for role in user_json['roles']:
            self.assertIn('id', role)
            self.assertIn(role['name'], ['role1', 'role2', 'role3'])
            self.assertListEqual(role['pages'], [])
            self.assertEqual(role['description'], '')

    def test_as_json_with_user_history(self):
        role_names = TestUserRolesDatabase.add_roles_to_db(3)
        user = User('username', 'password')
        db.session.add(user)
        user.set_roles(role_names)
        user.login('192.168.0.1')
        first_login_timestamp = datetime.utcnow()
        user.login('192.168.0.2')
        second_login_timestamp = datetime.utcnow()
        user_json = user.as_json(with_user_history=True)
        expected = {"id": 1,
                    "username": 'username',
                    "roles": [{'name': role, 'description': '', 'pages': []} for role in ['role1', 'role2', 'role3']],
                    "active": True,
                    "last_login_at": first_login_timestamp,
                    "current_login_at": second_login_timestamp,
                    "last_login_ip": '192.168.0.1',
                    "current_login_ip": '192.168.0.2',
                    "login_count": 2}
        self.assertSetEqual(set(user_json.keys()), set(expected.keys()))
        for key in ['username', 'active', 'last_login_ip', 'current_login_ip', 'login_count']:
            self.assertEqual(user_json[key], expected[key], '{} for user\'s json in incorrect'.format(key))

        self.assertAlmostEqual(user_json['last_login_at'], first_login_timestamp, delta=timedelta(milliseconds=100))
        self.assertAlmostEqual(user_json['current_login_at'], second_login_timestamp, delta=timedelta(milliseconds=100))
        for role in user_json['roles']:
            self.assertIn('id', role)
            self.assertIn(role['name'], ['role1', 'role2', 'role3'])
            self.assertListEqual(role['pages'], [])
            self.assertEqual(role['description'], '')

    def test_roles_as_json_with_users_one_user(self):
        role = Role('role1')
        db.session.add(role)
        user = User('username', 'password')
        db.session.add(user)
        user.set_roles(['role1'])
        expected = {'name': 'role1', 'description': '', 'pages': [], 'users': ['username']}
        role_json = role.as_json(with_users=True)
        role_json.pop('id')
        self.assertDictEqual(role_json, expected)

    def test_roles_as_json_with_users_multiple_users(self):
        role = Role('role1')
        db.session.add(role)
        user = User('username', 'password')
        user2 = User('user2', 'thisisagreatpassword')
        db.session.add(user)
        db.session.add(user2)
        user.set_roles(['role1'])
        user2.set_roles(['role1'])
        expected = {'name': 'role1', 'description': '', 'pages': [], 'users': ['username', 'user2']}
        role_json = role.as_json(with_users=True)
        role_json.pop('id')
        self.assertDictEqual(role_json, expected)