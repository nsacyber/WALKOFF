from unittest import TestCase

from server.database import db, User, Role
from server import flaskserver
from server.security import (user_has_correct_roles, roles_accepted, roles_required, permissions_accepted_for_resources,
                             permissions_required_for_resources, ResourcePermissions)


class TestSecurityDecorators(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = flaskserver.app.test_request_context()
        cls.context.push()
        db.create_all()

    def setUp(self):
        self.role1 = Role('role1')
        self.role2 = Role('role2')
        db.session.add(self.role1)
        db.session.add(self.role2)
        db.session.commit()
        self.user_role_one = User('username', 'password1', roles=['role1'])
        self.user_no_roles = User('username2', 'password2')
        db.session.add(self.user_role_one)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    def test_user_has_correct_identity_any_accepted_no_roles_accepted(self):
        self.assertFalse(user_has_correct_roles({}, user_id=self.user_role_one.id))

    def test_user_has_correct_identity_any_accepted_single_role_accepted(self):
        self.assertTrue(user_has_correct_roles({self.role1.name}, user_id=self.user_role_one.id))

    def test_user_has_correct_identity_any_accepted_multiple_roles_accepted(self):
        self.assertTrue(user_has_correct_roles({self.role1.name, self.role2.name}, user_id=self.user_role_one.id))

    def test_user_has_correct_identity_any_accepted_no_user_roles_none_accepted(self):
        user_no_roles = User('username3', 'password5')
        db.session.add(user_no_roles)
        db.session.commit()
        self.assertFalse(user_has_correct_roles(set(), user_id=user_no_roles.id))

    def test_user_has_correct_identity_any_accepted_no_user_roles_some_accepted(self):
        user_no_roles = User('username3', 'password5')
        db.session.add(user_no_roles)
        db.session.commit()
        self.assertFalse(user_has_correct_roles({self.role2.name, self.role1.name}, user_id=user_no_roles.id))

    def test_user_has_correct_identity_any_accepted_some_user_roles_different_accepted(self):
        user_no_roles = User('username3', 'password5')
        db.session.add(user_no_roles)
        db.session.commit()
        self.assertFalse(user_has_correct_roles({self.role2.name}, user_id=user_no_roles.id))

    def test_user_has_correct_identity_all_required_no_roles_required(self):
        self.assertFalse(user_has_correct_roles(set(), user_id=self.user_role_one.id, all_required=True))

    def test_user_has_correct_identity_all_required_single_role_required(self):
        self.assertTrue(user_has_correct_roles({self.role1.name}, user_id=self.user_role_one.id, all_required=True))

    def test_user_has_correct_identity_all_required_multiple_roles_required(self):
        self.assertFalse(user_has_correct_roles({self.role1.name, self.role2.name}, user_id=self.user_role_one.id, all_required=True))

    def test_user_has_correct_identity_all_required_no_user_roles_none_required(self):
        user_no_roles = User('username3', 'password5')
        db.session.add(user_no_roles)
        db.session.commit()
        self.assertFalse(user_has_correct_roles(set(), user_id=user_no_roles.id, all_required=True))

    def test_user_has_correct_identity_all_required_no_user_roles_some_required(self):
        user_no_roles = User('username3', 'password5')
        db.session.add(user_no_roles)
        db.session.commit()
        self.assertFalse(user_has_correct_roles({self.role2.name, self.role1.name}, user_id=user_no_roles.id, all_required=True))

    def test_user_has_correct_identity_all_required_some_user_roles_different_required(self):
        user_no_roles = User('username3', 'password5')
        db.session.add(user_no_roles)
        db.session.commit()
        self.assertFalse(user_has_correct_roles({self.role2.name}, user_id=user_no_roles.id, all_required=True))

    def test_user_has_correct_identity_all_required_some_user_roles_all_required(self):
        user_both_roles = User('username3', 'password5', roles=[self.role1.name, self.role2.name])
        db.session.add(user_both_roles)
        db.session.commit()
        self.assertTrue(user_has_correct_roles({self.role2.name, self.role1.name}, user_id=user_both_roles.id, all_required=True))

