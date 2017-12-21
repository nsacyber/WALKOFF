from unittest import TestCase
from server.endpoints.triggers import get_authorized_uids, add_user_in_progress
import server.messaging


class TestTriggerHelpers(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.uid1 = 'uid1'
        cls.uid2 = 'uid2'
        cls.uid3 = 'uid3'
        cls.uids = {cls.uid1, cls.uid2, cls.uid3}

    def tearDown(self):
        for uid in self.uids:
            server.messaging.workflow_authorization_cache.remove_authorizations(uid)

    def test_get_authorized_uids_no_uids_supplied(self):
        self.assertTupleEqual(get_authorized_uids(set(), 42, [3, 4]), (set(), set()))

    def test_get_authorized_uids_no_authorizations_required(self):
        self.assertTupleEqual(get_authorized_uids(self.uids, 42, [3, 4]), (self.uids, set()))

    def test_get_authorized_uids_all_require_authorizations(self):
        for uid in self.uids:
            server.messaging.workflow_authorization_cache.add_authorized_users(uid, [42], [3, 5])
        self.assertTupleEqual(get_authorized_uids(self.uids, 42, [3, 4]), (set(), self.uids))

    def test_get_authorized_users_some_not_authorized(self):
        server.messaging.workflow_authorization_cache.add_authorized_users('uid1', [42], [3, 5])
        server.messaging.workflow_authorization_cache.add_authorized_users('uid2', [42], [])
        server.messaging.workflow_authorization_cache.add_authorized_users('uid3', [84], [])
        self.assertTupleEqual(get_authorized_uids(self.uids, 42, [3, 4]), (set(), {self.uid1, self.uid2}))

    def test_get_authorized_users_mixed(self):
        server.messaging.workflow_authorization_cache.add_authorized_users('uid1', [42], [3, 5])
        server.messaging.workflow_authorization_cache.add_authorized_users('uid3', [84], [])
        self.assertTupleEqual(get_authorized_uids(self.uids, 42, [3, 4]), ({self.uid2}, {self.uid1}))

    def test_add_user_in_progress_no_users(self):
        for uid in self.uids:
            server.messaging.workflow_authorization_cache.add_authorized_users(uid, [42], [3, 5])
        add_user_in_progress(set(), 42)
        for uid in self.uids:
            self.assertIsNone(server.messaging.workflow_authorization_cache.peek_user_in_progress(uid))

    def test_add_user_in_progress(self):
        for uid in self.uids:
            server.messaging.workflow_authorization_cache.add_authorized_users(uid, [42], [3, 5])
        in_progress = (self.uid1, self.uid2)
        add_user_in_progress(in_progress, 42)
        for uid in in_progress:
            self.assertTrue(server.messaging.workflow_authorization_cache.peek_user_in_progress(uid), 42)
        self.assertIsNone(server.messaging.workflow_authorization_cache.peek_user_in_progress(self.uid3))

