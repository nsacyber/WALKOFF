import copy
import unittest

import walkoff.case.database as db
import walkoff.case.subscription as subs


class TestCases(unittest.TestCase):
    def setUp(self):
        subs.clear_subscriptions()
        self.cases1 = {'case1': {'uid1': ['e1', 'e2', 'e3'],
                                 'uid2': ['e1']},
                       'case2': {'uid1': ['e2', 'e3']}}
        self.cases_overlap = {'case2': {'uid3': ['e', 'b', 'c'],
                                        'uid4': ['d']},
                              'case3': {'uid1': ['a', 'b']}}
        self.cases2 = {'case3': {'uid3': ['e', 'b', 'c'],
                                 'uid4': ['d']},
                       'case4': {'uid1': ['a', 'b']}}

    def tearDown(self):
        subs.clear_subscriptions()
        # db.case_db.session.query(db.Case).delete()
        for case in db.case_db.session.query(db.Case).all():
            db.case_db.session.delete(case)
        db.case_db.session.commit()

    @staticmethod
    def get_case_names_in_database():
        return {x[0] for x in db.case_db.session.query(db.Case).with_entities(db.Case.name).all()}

    def assertDatabaseCasesAreCorrect(self, expected_cases):
        self.assertSetEqual(TestCases.get_case_names_in_database(), expected_cases)

    def assertInMemoryCasesAreCorrect(self, expected_cases):
        self.assertDictEqual(subs.subscriptions, expected_cases)

    def test_set_subscriptions_no_existing_cases_sets(self):
        subs.set_subscriptions(self.cases1)
        self.assertInMemoryCasesAreCorrect(self.cases1)
        self.assertDatabaseCasesAreCorrect({'case1', 'case2'})

    def test_set_subscriptions_with_existing_cases_sets(self):
        subs.subscriptions = self.cases1
        subs.set_subscriptions(self.cases_overlap)
        self.assertInMemoryCasesAreCorrect(self.cases_overlap)
        self.assertDatabaseCasesAreCorrect({'case2', 'case3'})

    def test_add_case_no_existing_cases_sets(self):
        subs.add_cases(self.cases1)
        self.assertInMemoryCasesAreCorrect(self.cases1)
        self.assertDatabaseCasesAreCorrect({'case1', 'case2'})

    def test_add_case_with_existing_cases_sets(self):
        subs.set_subscriptions(self.cases1)
        subs.add_cases(self.cases2)
        self.assertInMemoryCasesAreCorrect(self.cases1)
        self.assertDatabaseCasesAreCorrect({'case1', 'case2', 'case3', 'case4'})

    def test_delete_cases_no_existing_cases_is_empty(self):
        subs.delete_cases(['case1', 'case2'])
        self.assertInMemoryCasesAreCorrect({})
        self.assertDatabaseCasesAreCorrect(set())

    def test_delete_cases_all_existing_cases_is_empty(self):
        subs.set_subscriptions(self.cases1)
        subs.delete_cases(['case1', 'case2'])
        self.assertInMemoryCasesAreCorrect({})
        self.assertDatabaseCasesAreCorrect(set())

    def test_delete_cases_some_existing(self):
        subs.set_subscriptions(self.cases1)
        subs.add_cases(self.cases2)
        subs.delete_cases(['case2', 'case3'])
        expected_cases = {'case1': self.cases1['case1'], 'case4': self.cases2['case4']}
        self.assertInMemoryCasesAreCorrect(expected_cases)
        self.assertDatabaseCasesAreCorrect(set(expected_cases.keys()))

    def test_rename_case(self):
        cases = copy.deepcopy(self.cases1)
        subs.set_subscriptions(self.cases1)
        self.assertTrue(subs.rename_case('case1', 'renamed'))
        cases['renamed'] = cases.pop('case1')
        self.assertInMemoryCasesAreCorrect(cases)
        self.assertDatabaseCasesAreCorrect({'renamed', 'case2'})

    def test_rename_case_no_existing_case(self):
        cases = copy.deepcopy(self.cases1)
        subs.set_subscriptions(self.cases1)
        self.assertFalse(subs.rename_case('invalid', 'renamed'))
        self.assertInMemoryCasesAreCorrect(cases)
        self.assertDatabaseCasesAreCorrect({'case1', 'case2'})

    def test_rename_case_to_existing_case(self):
        cases = copy.deepcopy(self.cases1)
        subs.set_subscriptions(self.cases1)
        self.assertFalse(subs.rename_case('case1', 'case2'))
        self.assertInMemoryCasesAreCorrect(cases)
        self.assertDatabaseCasesAreCorrect({'case1', 'case2'})

    def test_rename_case_no_cases(self):
        self.assertFalse(subs.rename_case('case1', 'renamed'))
        self.assertInMemoryCasesAreCorrect({})
        self.assertDatabaseCasesAreCorrect(set())

    def test_clear_subscriptions_no_cases(self):
        subs.clear_subscriptions()
        self.assertInMemoryCasesAreCorrect({})
        self.assertDatabaseCasesAreCorrect(set())

    def test_clear_subscriptions(self):
        subs.set_subscriptions(self.cases1)
        subs.clear_subscriptions()
        self.assertInMemoryCasesAreCorrect({})
        self.assertDatabaseCasesAreCorrect(set())

    def test_get_cases_subscribed_no_cases(self):
        self.assertSetEqual(set(subs.get_cases_subscribed('uid1', 'e')), set())

    def test_get_cases_subscribed_no_uid_found(self):
        subs.set_subscriptions(self.cases1)
        self.assertSetEqual(set(subs.get_cases_subscribed('invalid', 'e')), set())

    def test_get_cases_subscribed_no_event_found(self):
        subs.set_subscriptions(self.cases1)
        self.assertSetEqual(set(subs.get_cases_subscribed('uid1', 'invalid')), set())

    def test_get_cases_subscribed_one_case_one_case_found(self):
        subs.set_subscriptions(self.cases2)
        self.assertSetEqual(set(subs.get_cases_subscribed('uid4', 'd')), {'case3'})

    def test_get_cases_subscribed_multiple_cases_one_event_found(self):
        subs.set_subscriptions(self.cases1)
        self.assertSetEqual(set(subs.get_cases_subscribed('uid1', 'e2')), {'case1', 'case2'})

    def test_modify_subscriptions_no_cases(self):
        subs.modify_subscription('case1', 'uid1', ['e1', 'e3'])
        self.assertInMemoryCasesAreCorrect({})

    def test_modify_subscriptions_case_not_found(self):
        cases = copy.deepcopy(self.cases1)
        subs.set_subscriptions(self.cases1)
        subs.modify_subscription('invalid', 'uid1', ['e1', 'e3'])
        self.assertInMemoryCasesAreCorrect(cases)

    def test_modify_subscriptions_uid_not_found(self):
        cases = copy.deepcopy(self.cases1)
        subs.set_subscriptions(self.cases1)
        subs.modify_subscription('case1', 'new_uid', ['e1', 'e3'])
        cases['case1']['new_uid'] = ['e1', 'e3']
        self.assertInMemoryCasesAreCorrect(cases)

    def test_modify_subscriptions_new_subscriptions(self):
        cases = copy.deepcopy(self.cases1)
        subs.set_subscriptions(self.cases1)
        subs.modify_subscription('case1', 'uid1', ['e1', 'e3'])
        cases['case1']['uid1'] = ['e1', 'e3']
        self.assertInMemoryCasesAreCorrect(cases)

    def test_remove_subscription_node_no_cases(self):
        subs.remove_subscription_node('invalid', 'uid1')
        self.assertInMemoryCasesAreCorrect({})

    def test_remove_subscription_node_case_not_found(self):
        cases = copy.deepcopy(self.cases1)
        subs.set_subscriptions(self.cases1)
        subs.remove_subscription_node('invalid', 'uid1')
        self.assertInMemoryCasesAreCorrect(cases)

    def test_remove_subscription_node(self):
        cases = copy.deepcopy(self.cases1)
        subs.set_subscriptions(self.cases1)
        subs.remove_subscription_node('case1', 'uid1')
        cases['case1'].pop('uid1')
        self.assertInMemoryCasesAreCorrect(cases)
