import json
import unittest
from server.casesubscription import CaseSubscription


class TestCaseConfigDatabase(unittest.TestCase):

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
        expected_json = {'name': 'name', 'subscriptions': {}}
        self.assertDictEqual(case.as_json(), expected_json)
        derived_json = CaseSubscription.from_json('name', {}).as_json()
        self.assertDictEqual(derived_json, expected_json)

        case = CaseSubscription('name', '{{')
        expected_json = {'name': 'name', 'subscriptions': {}}
        self.assertDictEqual(case.as_json(), expected_json)

        test_json = {"a": {"b": {"c": []},
                           "d": ["e", "f", "g"]}}
        case = CaseSubscription('name', json.dumps(test_json))
        expected_json = {'name': 'name', 'subscriptions': test_json}
        self.assertDictEqual(case.as_json(), expected_json)
        derived_json = CaseSubscription.from_json('name', test_json).as_json()
        self.assertDictEqual(derived_json, expected_json)
