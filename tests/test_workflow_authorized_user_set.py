from unittest import TestCase
from walkoff.messaging import WorkflowAuthorizedUserSet


class TestWorkflowAuthorizedUserSet(TestCase):

    def test_is_authorized(self):
        users = ['user1', 'user2']
        roles = ['admin', 'guest']
        authorizations = WorkflowAuthorizedUserSet(users=users, roles=roles)
        for user in users:
            self.assertTrue(authorizations.is_authorized(user, 'visitor'))
        for role in roles:
            self.assertTrue(authorizations.is_authorized('user3', role))
        self.assertTrue(authorizations.is_authorized('user1', 'admin'))
        self.assertFalse(authorizations.is_authorized('user3', 'visitor'))

    def test_add_authorizations_no_overlap(self):
        users1 = ['user1', 'user2']
        roles1 = ['admin', 'guest']
        authorizations = WorkflowAuthorizedUserSet(users=users1, roles=roles1)
        users2 = ['user3', 'user4']
        roles2 = ['admin2', 'guest2']

        authorizations.add(users=users2, roles=roles2)
        for user in users1 + users2:
            self.assertTrue(authorizations.is_authorized(user, 'visitor'))
        for role in roles1 + roles2:
            self.assertTrue(authorizations.is_authorized('user10', role))

    def test_add_authorizations_with_overlap(self):
        users1 = ['user1', 'user2']
        roles1 = ['admin', 'guest']
        authorizations = WorkflowAuthorizedUserSet(users=users1, roles=roles1)
        users2 = ['user2', 'user3']
        roles2 = ['admin', 'guest2']
        authorizations.add(users=users2, roles=roles2)
        for user in ['user1', 'user2', 'user3']:
            self.assertTrue(authorizations.is_authorized(user, 'visitor'))
        for role in ['admin', 'guest', 'guest2']:
            self.assertTrue(authorizations.is_authorized('user10', role))

    def test_add_authorizations_no_roles(self):
        users1 = ['user1', 'user2']
        roles1 = ['admin', 'guest']
        authorizations = WorkflowAuthorizedUserSet(users=users1, roles=roles1)
        users2 = ['user2', 'user3']
        authorizations.add(users=users2)
        for user in ['user1', 'user2', 'user3']:
            self.assertTrue(authorizations.is_authorized(user, 'visitor'))
        for role in ['admin', 'guest']:
            self.assertTrue(authorizations.is_authorized('user10', role))
        self.assertFalse(authorizations.is_authorized(None, 'admin'))
        self.assertFalse(authorizations.is_authorized('user1', None))

    def test_add_authorizations_no_users(self):
        users1 = ['user1', 'user2']
        roles1 = ['admin', 'guest']
        authorizations = WorkflowAuthorizedUserSet(users=users1, roles=roles1)
        roles2 = ['admin', 'guest2']
        authorizations.add(roles=roles2)
        for user in ['user1', 'user2']:
            self.assertTrue(authorizations.is_authorized(user, 'visitor'))
        for role in ['admin', 'guest', 'guest2']:
            self.assertTrue(authorizations.is_authorized('user10', role))
        self.assertFalse(authorizations.is_authorized(None, 'admin'))
        self.assertFalse(authorizations.is_authorized('user1', None))
