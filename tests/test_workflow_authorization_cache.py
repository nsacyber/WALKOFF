from unittest import TestCase
from server.messaging import WorkflowAuthorizationCache


class TestWorkflowAuthorizationCache(TestCase):

    def setUp(self):
        self.cache = WorkflowAuthorizationCache()

    def test_add_authorized_users(self):
        users = [1, 2, 3]
        roles = [1, 2]
        self.cache.add_authorized_users('workflow_uid1', users=users, roles=roles)
        for user in users:
            self.assertTrue(self.cache.is_authorized('workflow_uid1', user, 1))
            self.assertFalse(self.cache.is_authorized('workflow_uid2', user, 1))
        for role in roles:
            self.assertTrue(self.cache.is_authorized('workflow_uid1', 1, role))
            self.assertFalse(self.cache.is_authorized('workflow_uid2', 1, role))
        self.assertFalse(self.cache.is_authorized('workflow_uid1', 4, 4))
