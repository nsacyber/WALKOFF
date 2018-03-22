import unittest
from uuid import uuid4

from walkoff.case.subscription import SubscriptionCache, Subscription


class TestCaseSubscriptions(unittest.TestCase):

    def setUp(self):
        self.subs = SubscriptionCache()
        self.ids = [uuid4() for _ in range(4)]
        self.case1 = [Subscription(self.ids[0], ['e1', 'e2', 'e3']),
                      Subscription(self.ids[1], ['e1'])]
        self.case2 = [Subscription(self.ids[0], ['e2', 'e3'])]
        self.case3 = [Subscription(self.ids[2], ['e', 'b', 'c']),
                      Subscription(self.ids[3], ['d'])]
        self.case4 = [Subscription(self.ids[0], ['a', 'b'])]

    def assert_events_have_cases(self, sender_id, events, cases, not_in=False):
        for event in events:
            for case in cases:
                if not_in:
                    self.assertNotIn(case, self.subs._subscriptions[sender_id][event])
                else:
                    self.assertIn(case, self.subs._subscriptions[sender_id][event])

    def assert_case_is_cached(self, case, case_name, not_in=False):
        for sub in case:
            self.assert_events_have_cases(sub.id, sub.events, {case_name}, not_in=not_in)

    def test_add_from_empty_cache(self):
        self.subs.add_subscriptions(1, self.case1)
        self.assert_case_is_cached(self.case1, 1)

    def test_add_with_same_cases(self):
        self.subs.add_subscriptions(1, self.case1)
        self.subs.add_subscriptions(1, self.case1)
        self.assert_case_is_cached(self.case1, 1)

    def test_add_same_case_different_name(self):
        for case in (1, 2):
            self.subs.add_subscriptions(case, self.case1)
        for case in (1, 2):
            self.assert_case_is_cached(self.case1, case)

    def test_add_multiple_cases(self):
        cases = {1: self.case1, 2: self.case2, 'case3': self.case3, 'case4': self.case4}
        for case_name, case in cases.items():
            self.subs.add_subscriptions(case_name, case)
        for case_name, case in cases.items():
            self.assert_case_is_cached(case, case_name)

    def test_update_from_empty_cache(self):
        self.subs.update_subscriptions(1, self.case1)
        self.assert_case_is_cached(self.case1, 1)

    def test_update_with_same_cases(self):
        self.subs.update_subscriptions(1, self.case1)
        self.subs.update_subscriptions(1, self.case1)
        self.assert_case_is_cached(self.case1, 1)

    def test_update_same_case_different_name(self):
        for case in (1, 2):
            self.subs.update_subscriptions(case, self.case1)
        for case in (1, 2):
            self.assert_case_is_cached(self.case1, case)

    def test_update_case_erases_old_subs(self):
        self.subs.add_subscriptions(1, [Subscription(self.ids[0], ['e1', 'e2', 'e3'])])
        self.subs.add_subscriptions(2, [Subscription(self.ids[0], ['e1', 'e2', 'e4'])])
        self.subs.update_subscriptions(1, [Subscription(self.ids[0], ['e1', 'e2'])])
        self.assert_events_have_cases(self.ids[0], ['e1', 'e2'], {1, 2})
        self.assert_events_have_cases(self.ids[0], ['e4'], {2})
        self.assertNotIn('e3', self.subs._subscriptions[self.ids[0]])

    def test_get_cases_subscribed_empty_cache(self):
        self.assertSetEqual(self.subs.get_cases_subscribed(uuid4(), 'event'), set())

    def test_get_cases_subscribed_no_such_event(self):
        self.subs.add_subscriptions(1, self.case2)
        self.assertSetEqual(self.subs.get_cases_subscribed(self.ids[0], 'invalid'), set())

    def test_get_cases_subscribed_one_case(self):
        self.subs.add_subscriptions(1, self.case2)
        self.assertSetEqual(self.subs.get_cases_subscribed(self.ids[0], 'e2'), {1})

    def test_get_cases_subscribed_multiple_case(self):
        self.subs.add_subscriptions(1, self.case2)
        self.subs.add_subscriptions(2, self.case2)
        self.assertSetEqual(self.subs.get_cases_subscribed(self.ids[0], 'e2'), {1, 2})

    def test_remove_cases(self):
        for case in (1, 2):
            self.subs.add_subscriptions(case, self.case1)
        self.subs.delete_case(1)
        self.assert_case_is_cached(self.case1, 2)
        self.assert_case_is_cached(self.case1, 1, not_in=True)

    def test_remove_cases_no_matching_case(self):
        self.subs.add_subscriptions(1, self.case1)
        self.subs.delete_case(42)
        self.assert_case_is_cached(self.case1, 1)

    def test_clear(self):
        self.subs.update_subscriptions(1, self.case1)
        self.subs.clear()
        self.assertDictEqual(self.subs._subscriptions, {})
