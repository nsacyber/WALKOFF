from unittest import TestCase

from walkoff.messaging import WorkflowAuthorizationCache


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

    def test_add_authorized_users_workflow_already_exists(self):
        users = [1, 2, 3]
        roles = [1, 2]
        self.cache.add_authorized_users('workflow_uid1', users=users, roles=roles)
        users2 = [4, 5]
        roles2 = [3]
        self.cache.add_authorized_users('workflow_uid1', users=users2, roles=roles2)
        for user in users + users2:
            self.assertTrue(self.cache.is_authorized('workflow_uid1', user, 1))
            self.assertFalse(self.cache.is_authorized('workflow_uid2', user, 1))
        for role in roles + roles2:
            self.assertTrue(self.cache.is_authorized('workflow_uid1', 1, role))
            self.assertFalse(self.cache.is_authorized('workflow_uid2', 1, role))
        self.assertFalse(self.cache.is_authorized('workflow_uid1', 6, 6))

    def test_is_authorized_no_corresponding_workflow(self):
        self.assertFalse(self.cache.is_authorized('workflow2', 1, 1))

    def test_remove_authorization(self):
        self.cache.add_authorized_users('workflow_uid1', users=[1], roles=[2])
        self.cache.remove_authorizations('workflow_uid1')
        self.assertFalse(self.cache.workflow_requires_authorization('workflow_uid1'))

    def test_workflow_requires_authorization(self):
        self.cache.add_authorized_users('workflow_uid1', users=[1], roles=[2])
        self.assertTrue(self.cache.workflow_requires_authorization('workflow_uid1'))
        self.assertFalse(self.cache.workflow_requires_authorization('workflow_uid2'))

    def test_add_user_in_progress_workflow_not_in_cache(self):
        self.cache.add_user_in_progress('uid1', 1)
        self.assertIsNone(self.cache.peek_user_in_progress('uid1'))

    def test_add_user_in_progress(self):
        self.cache.add_authorized_users('uid1', users=[1])
        self.cache.add_user_in_progress('uid1', 1)
        self.assertEqual(self.cache.peek_user_in_progress('uid1'), 1)
        self.cache.add_user_in_progress('uid1', 3)
        self.assertEqual(self.cache.peek_user_in_progress('uid1'), 3)

    def test_pop_user_in_progress_workflow_not_in_cache(self):
        self.assertIsNone(self.cache.pop_last_user_in_progress('uid1'))

    def test_pop_user_in_progress_empty_queue(self):
        self.cache.add_authorized_users('uid1', users=[1])
        self.assertIsNone(self.cache.pop_last_user_in_progress('uid1'))

    def test_pop_user_in_progress(self):
        self.cache.add_authorized_users('uid1', users=[1])
        self.cache.add_user_in_progress('uid1', 1)
        self.assertEqual(self.cache.pop_last_user_in_progress('uid1'), 1)
        self.cache.add_user_in_progress('uid1', 7)
        self.assertEqual(self.cache.pop_last_user_in_progress('uid1'), 7)
