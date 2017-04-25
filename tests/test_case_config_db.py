import json
from core.case.subscription import set_subscriptions, subscriptions_as_json, clear_subscriptions
from server.casesubscription import CaseSubscription
from tests.util.servertestcase import ServerTestCase
from tests.util.case import construct_case1, construct_case2
from server import flaskserver as server


class TestCaseConfigDatabase(ServerTestCase):

    def tearDown(self):
        clear_subscriptions()
        for case in server.running_context.CaseSubscription.query.all():
            server.running_context.db.session.delete(case)
        server.running_context.db.session.commit()

    def __help_test_init(self, case, name, subscription):
        self.assertIsNotNone(case)
        self.assertEqual(case.name, name)
        self.assertEqual(case.subscription, subscription)

    def test_init(self):
        case = CaseSubscription('name')
        self.__help_test_init(case, 'name', '{}')

        case = CaseSubscription('name', '{{')
        self.__help_test_init(case, 'name', '{}')

        test_json = {"a": {"b": {"c": []},
                           "d": ["e", "f", "g"]}}
        case = CaseSubscription('name', json.dumps(test_json))
        self.__help_test_init(case, 'name', json.dumps(test_json))

    def test_to_from_json(self):
        case = CaseSubscription('name')
        expected_json = {'name': 'name', 'subscription': {}}
        self.assertDictEqual(case.as_json(), expected_json)
        derived_json = CaseSubscription.from_json('name', {}).as_json()
        self.assertDictEqual(derived_json, expected_json)

        case = CaseSubscription('name', '{{')
        expected_json = {'name': 'name', 'subscription': {}}
        self.assertDictEqual(case.as_json(), expected_json)

        test_json = {"a": {"b": {"c": []},
                           "d": ["e", "f", "g"]}}
        case = CaseSubscription('name', json.dumps(test_json))
        expected_json = {'name': 'name', 'subscription': test_json}
        self.assertDictEqual(case.as_json(), expected_json)
        derived_json = CaseSubscription.from_json('name', test_json).as_json()
        self.assertDictEqual(derived_json, expected_json)

    def test_sync_to_subscriptions(self):
        case1, _ = construct_case1()
        case2, _ = construct_case2()
        case3, _ = construct_case2()
        case4, _ = construct_case1()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        case_db_entry_1 = CaseSubscription('case3', subscription=json.dumps(case3.as_json()))
        case_db_entry_2 = CaseSubscription('case4', subscription=json.dumps(case4.as_json()))
        server.running_context.db.session.add(case_db_entry_1)
        server.running_context.db.session.add(case_db_entry_2)
        server.running_context.db.session.commit()
        CaseSubscription.sync_to_subscriptions()
        result_subscriptions = subscriptions_as_json()
        self.assertIn('case3', result_subscriptions)
        self.assertIn('case4', result_subscriptions)
        self.assertNotIn('case1', result_subscriptions)
        self.assertNotIn('case2', result_subscriptions)
        self.assertDictEqual(result_subscriptions['case3'], case3.as_json())
        self.assertDictEqual(result_subscriptions['case4'], case4.as_json())


