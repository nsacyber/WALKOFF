from unittest import TestCase
from server.messaging import WorkflowAuthorization


class TestWorkflowAuthorization(TestCase):

    def test_is_authorized(self):
        users = [1, 2, 3]
        roles = [3, 4]
        auth = WorkflowAuthorization(users, roles)
        for user in users:
            self.assertTrue(auth.is_authorized(user, 3))
        for role in roles:
            self.assertTrue(auth.is_authorized(1, role))
        self.assertFalse(auth.is_authorized(4, 5))
        self.assertFalse(auth.is_authorized(10, 10))

    def test_add_authorized_users(self):
        users = [1, 2, 3]
        roles = [3, 4]
        auth = WorkflowAuthorization(users, roles)
        users2 = [5, 6]
        roles2 = [1, 2]
        auth.add_authorizations(users2, roles2)
        for user in users + users2:
            self.assertTrue(auth.is_authorized(user, 3))
        for role in roles + roles2:
            self.assertTrue(auth.is_authorized(1, role))

    def test_append_user(self):
        users = [1, 2, 3]
        roles = [3, 4]
        auth = WorkflowAuthorization(users, roles)
        auth.append_user(1)
        self.assertEqual(auth.peek_user(), 1)
        auth.append_user(5)
        self.assertEqual(auth.peek_user(), 5)

    def test_pop_user(self):
        users = [1, 2, 3]
        roles = [3, 4]
        auth = WorkflowAuthorization(users, roles)
        auth.append_user(1)
        auth.append_user(5)
        self.assertEqual(auth.pop_user(), 5)
        self.assertEqual(auth.pop_user(), 1)
