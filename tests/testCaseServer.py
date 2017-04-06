import unittest
import json
from tests.util.case import construct_case1, construct_case2, construct_case_json
import core.case.database as case_database
from core.case.subscription import set_subscriptions, clear_subscriptions, CaseSubscriptions, \
    GlobalSubscriptions, subscriptions_as_json, Subscription
from core.executionelement import ExecutionElement
from core.case.callbacks import _EventEntry
from server import flaskServer as flask_server
from os.path import join


class TestCaseServer(unittest.TestCase):
    def setUp(self):
        case_database.initialize()
        self.app = flask_server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}

    def tearDown(self):
        case_database.case_db.tearDown()
        clear_subscriptions()

    @staticmethod
    def __basic_case_setup():
        case1, _ = construct_case1()
        case2, _ = construct_case2()
        case3, _ = construct_case1()
        case4, _ = construct_case2()
        cases = {'case1': case1, 'case2': case2, 'case3': case3, 'case4': case4}
        set_subscriptions(cases)
        return cases

    def test_display_cases_typical(self):
        cases = TestCaseServer.__basic_case_setup()
        response = self.app.get('/cases', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases = set(cases.keys())
        received_cases = [case['name'] for case in response['cases']]
        self.assertEqual(len(expected_cases), len(received_cases), 'Received unexpected number of cases')
        self.assertSetEqual(expected_cases, set(received_cases), 'Received incorrect cases')

    def test_display_cases_none(self):
        response = self.app.get('/cases', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases = []
        received_cases = [case['name'] for case in response['cases']]
        self.assertEqual(len(expected_cases), len(received_cases), 'Received unexpected number of cases')
        self.assertSetEqual(set(expected_cases), set(received_cases), 'Received incorrect cases')

    def test_display_case_not_found(self):
        response = self.app.get('/cases/hiThere', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        with self.assertRaises(KeyError):
            _ = response['cases']
        self.assertEqual(response['status'], 'Case with given name does not exist',
                         'Received unexpected number of cases')

    def test_display_case(self):
        TestCaseServer.__basic_case_setup()

        elem1 = ExecutionElement(name='b', parent_name='a')
        elem2 = ExecutionElement(name='c', parent_name='b', ancestry=['a', 'b', 'c'])
        elem3 = ExecutionElement(name='d', parent_name='c')
        elem4 = ExecutionElement()

        event1 = _EventEntry(elem1, 'message1', 'SYSTEM')
        event2 = _EventEntry(elem2, 'message2', 'WORKFLOW')
        event3 = _EventEntry(elem3, 'message3', 'STEP')
        event4 = _EventEntry(elem4, 'message4', 'NEXT')

        case_database.case_db.add_event(event=event1, cases=['case1', 'case3'])
        case_database.case_db.add_event(event=event2, cases=['case2', 'case4'])
        case_database.case_db.add_event(event=event3, cases=['case2', 'case3', 'case4'])
        case_database.case_db.add_event(event=event4, cases=['case1'])

        def create_event_logs(events):
            return [case_database.Event(type=event.type,
                                        ancestry=','.join(map(str, event.ancestry)),
                                        message=event.message)
                    for event in events]

        def event_logs_as_json(events):
            return [event.as_json() for event in create_event_logs(events)]

        case_events = [('case1', [event1, event4]), ('case2', [event2, event3]),
                       ('case3', [event1, event3]), ('case4', [event2, event3])]

        expected_events_collection = {case_name: event_logs_as_json(events) for case_name, events in case_events}

        for case_name, expected_events in expected_events_collection.items():
            response = self.app.get('/cases/{0}'.format(case_name), headers=self.headers)
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            self.assertEqual(case_name, response['case']['name'], 'Received case name differs from expected')
            received_events = [{key: event[key] for key in ['type', 'message', 'ancestry']}
                               for event in response['case']['events']]
            expected_events = [{key: event[key] for key in ['type', 'message', 'ancestry']}
                               for event in expected_events]
            self.assertEqual(len(received_events), len(expected_events), 'Unexpected number of events receieved')
            for event in expected_events:
                self.assertTrue(event in received_events, 'Expected event is not in receieved events')

    def test_add_case_no_existing_cases(self):
        response = self.app.post('/cases/case1/add', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response, {'case1': CaseSubscriptions().as_json()})
        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        self.assertEqual(len(cases), len(expected_cases))
        self.assertSetEqual(set(expected_cases), set(cases))

    def test_add_case_existing_cases(self):
        case1 = CaseSubscriptions()
        set_subscriptions({'case1': case1})
        response = self.app.post('/cases/case2/add', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response, {'case1': CaseSubscriptions().as_json(),
                                    'case2': CaseSubscriptions().as_json()})
        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1', 'case2']
        self.assertEqual(len(cases), len(expected_cases))
        self.assertSetEqual(set(expected_cases), set(cases))

    def test_add_case_duplicate_case(self):
        global_subs = GlobalSubscriptions(controller=['a'])
        case1 = CaseSubscriptions(global_subscriptions=global_subs)
        set_subscriptions({'case1': case1})
        expected_json = subscriptions_as_json()
        response = self.app.post('/cases/case1/add', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response, expected_json)

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        self.assertEqual(len(cases), len(expected_cases))
        self.assertSetEqual(set(expected_cases), set(cases))

    def test_delete_case_only_case(self):
        case1 = CaseSubscriptions()
        set_subscriptions({'case1': case1})
        response = self.app.post('/cases/case1/delete', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response, {})

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = []
        self.assertEqual(len(cases), len(expected_cases))
        self.assertSetEqual(set(expected_cases), set(cases))

    def test_delete_case(self):
        case1 = CaseSubscriptions()
        case2 = CaseSubscriptions()
        set_subscriptions({'case1': case1, 'case2': case2})
        response = self.app.post('/cases/case1/delete', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response, {'case2': case2.as_json()})

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case2']
        self.assertEqual(len(cases), len(expected_cases))
        self.assertSetEqual(set(expected_cases), set(cases))

    def test_delete_case_invalid_case(self):
        case1 = CaseSubscriptions()
        case2 = CaseSubscriptions()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        response = self.app.post('/cases/case3/delete', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response, {name: case.as_json() for name, case in cases.items()})

        db_cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = list(cases.keys())
        self.assertEqual(len(db_cases), len(expected_cases))
        self.assertSetEqual(set(expected_cases), set(db_cases))

    def test_delete_case_no_cases(self):
        response = self.app.post('/cases/case1/delete', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response, {})

        db_cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = []
        self.assertEqual(len(db_cases), len(expected_cases))
        self.assertSetEqual(set(expected_cases), set(db_cases))

    def test_edit_case(self):
        case1 = CaseSubscriptions()
        case2 = CaseSubscriptions()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        original_cases_json = case_database.case_db.cases_as_json()
        data = {"name": "renamed",
                "note": "note1"}
        response = self.app.post('/cases/case1/edit', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))

        for case in original_cases_json['cases']:
            if case['name'] == 'case1':
                case['name'] = 'renamed'
                case['note'] = 'note1'
        result_cases = case_database.case_db.cases_as_json()
        self.assertDictEqual(result_cases, original_cases_json)
        self.assertDictEqual(response, original_cases_json)

    def test_edit_case_no_name(self):
        case1 = CaseSubscriptions()
        case2 = CaseSubscriptions()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        original_cases_json = case_database.case_db.cases_as_json()
        data = {"note": "note1"}
        response = self.app.post('/cases/case2/edit', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))

        for case in original_cases_json['cases']:
            if case['name'] == 'case2':
                case['note'] = 'note1'
        result_cases = case_database.case_db.cases_as_json()
        self.assertDictEqual(result_cases, original_cases_json)
        self.assertDictEqual(response, original_cases_json)

    def test_edit_case_no_note(self):
        case1 = CaseSubscriptions()
        case2 = CaseSubscriptions()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        original_cases_json = case_database.case_db.cases_as_json()
        data = {"name": "renamed"}
        response = self.app.post('/cases/case1/edit', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))

        for case in original_cases_json['cases']:
            if case['name'] == 'case1':
                case['name'] = 'renamed'
        result_cases = case_database.case_db.cases_as_json()
        self.assertDictEqual(result_cases, original_cases_json)
        self.assertDictEqual(response, original_cases_json)

    def test_edit_case_invalid_case(self):
        case1 = CaseSubscriptions()
        case2 = CaseSubscriptions()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        original_cases_json = case_database.case_db.cases_as_json()
        data = {"name": "renamed"}
        response = self.app.post('/cases/case3/edit', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))

        result_cases = case_database.case_db.cases_as_json()
        self.assertDictEqual(result_cases, original_cases_json)
        self.assertDictEqual(response, original_cases_json)

    def test_crud_case_invalid_action(self):
        response = self.app.post('/cases/case3/junk', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual({"status": "Invalid operation junk"}, response)

    def test_display_possible_subscriptions(self):
        with open(join('.', 'data', 'events.json')) as f:
            expected_response = json.loads(f.read())

        response = self.app.get('/cases/availablesubscriptions', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_response)

    def test_display_subscriptions(self):
        case1, accept1 = construct_case1()
        case2, accept2 = construct_case2()
        case3, accept3 = construct_case1()
        case4, accept4 = construct_case2()
        cases = {'case1': case1, 'case2': case2, 'case3': case3, 'case4': case4}
        set_subscriptions(cases)

        expected_response = {key: case.as_json() for key, case in cases.items()}

        response = self.app.get('/cases/subscriptions/', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(expected_response, response)

    def test_edit_global_subscription(self):
        global_subs1 = {"controller-0": 'a',
                        "controller-1": 'b',
                        "controller-2": 'c',
                        "controller-3": 'd',
                        "workflow-0": 'e',
                        "next_step-0": 'f',
                        "filter-0": 'g',
                        "filter-1": 'h',
                        "filter-2": 'i'}

        case1 = CaseSubscriptions()
        case2 = CaseSubscriptions()
        set_subscriptions({'case1': case1, 'case2': case2})

        response = self.app.post('/cases/subscriptions/case1/global/edit', data=global_subs1, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_global1 = GlobalSubscriptions(controller=['a', 'b', 'c', 'd'], workflow=['e'], next_step=['f'],
                                               filter=['g', 'h', 'i'])
        expected_case1 = CaseSubscriptions(global_subscriptions=expected_global1)
        expected_response = {'case1': expected_case1.as_json(), 'case2': case2.as_json()}
        self.assertDictEqual(expected_response, response)
        self.assertDictEqual(expected_response, subscriptions_as_json())

    def test_edit_global_subscription_invalid_case(self):
        global_subs = {"controller-0": 'a',
                       "controller-1": 'b',
                       "controller-2": 'c',
                       "controller-3": 'd',
                       "workflow-0": 'e',
                       "next_step-0": 'f',
                       "filter-0": 'g',
                       "filter-1": 'h',
                       "filter-2": 'i'}

        response = self.app.post('/cases/subscriptions/case1/global/edit', data=global_subs, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual({u'status': u'Error: Case name case1 was not found'}, response)

        case2 = CaseSubscriptions()
        set_subscriptions({'case2': case2})
        response = self.app.post('/cases/subscriptions/case1/global/edit', data=global_subs, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual({u'status': u'Error: Case name case1 was not found'}, response)

    def test_edit_subscription(self):
        sub1 = Subscription()
        sub2 = Subscription()
        sub3 = Subscription()

        sub4 = Subscription(subscriptions={'sub1': sub1, 'sub2': sub2})
        sub5 = Subscription(subscriptions={'sub3': sub3})
        sub6 = Subscription()

        sub7 = Subscription(subscriptions={'sub4': sub4})
        sub8 = Subscription(subscriptions={'sub5': sub5, 'sub6': sub6})

        case2 = CaseSubscriptions(subscriptions={'sub7': sub7, 'sub8': sub8})

        set_subscriptions({'case1': CaseSubscriptions(), 'case2': case2})

        edit1 = {"ancestry-0": "sub8",
                 "ancestry-1": "sub5",
                 "ancestry-2": "sub3",
                 "events-0": "a",
                 "events-1": "b"}

        edit2 = {"ancestry-0": "sub7",
                 "ancestry-1": "sub4",
                 "events-0": "c",
                 "events-1": "d",
                 "events-2": "e"}

        edit3 = {"ancestry-0": "sub8",
                 "events-0": "e"}

        tree = {'sub7': {'sub4': {'sub1': {},
                                  'sub2': {}}},
                'sub8': {'sub5': {'sub3': {}},
                         'sub6': {}}}

        expected_cases_json = {'case2': construct_case_json(tree), 'case1': CaseSubscriptions().as_json()}
        expected_cases_json['case2']['subscriptions']['sub8']['subscriptions']['sub5']['subscriptions']['sub3'][
            'events'] \
            = ['a', 'b']

        response = self.app.post('/cases/subscriptions/case2/subscription/edit', data=edit1, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)

        expected_cases_json['case2']['subscriptions']['sub7']['subscriptions']['sub4']['events'] \
            = ['c', 'd', 'e']

        response = self.app.post('/cases/subscriptions/case2/subscription/edit', data=edit2, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)

        expected_cases_json['case2']['subscriptions']['sub8']['events'] = ['e']

        response = self.app.post('/cases/subscriptions/case2/subscription/edit', data=edit3, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)

    def test_edit_subscription_invalid_ancestry(self):
        sub1 = Subscription()
        sub2 = Subscription()
        sub3 = Subscription()

        sub4 = Subscription(subscriptions={'sub1': sub1, 'sub2': sub2})
        sub5 = Subscription(subscriptions={'sub3': sub3})
        sub6 = Subscription()

        sub7 = Subscription(subscriptions={'sub4': sub4})
        sub8 = Subscription(subscriptions={'sub5': sub5, 'sub6': sub6})

        case2 = CaseSubscriptions(subscriptions={'sub7': sub7, 'sub8': sub8})

        set_subscriptions({'case1': CaseSubscriptions(), 'case2': case2})

        edit1 = {"ancestry-0": "sub8",
                 "ancestry-1": "sub5",
                 "ancestry-2": "junk",
                 "events-0": "a",
                 "events-1": "b"}

        response = self.app.post('/cases/subscriptions/case2/subscription/edit', data=edit1, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual({u'status': 'Error occurred while editing subscription'}, response)

    def test_edit_subscription_invalid_case(self):
        response = self.app.post('/cases/subscriptions/case1/subscription/edit', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual({u'status': 'Error occurred while editing subscription'}, response)

    def test_add_subscription(self):
        sub1 = Subscription()
        sub2 = Subscription()
        sub3 = Subscription()

        sub4 = Subscription(subscriptions={'sub1': sub1, 'sub2': sub2})
        sub5 = Subscription(subscriptions={'sub3': sub3})
        sub6 = Subscription()

        sub7 = Subscription(subscriptions={'sub4': sub4})
        sub8 = Subscription(subscriptions={'sub5': sub5, 'sub6': sub6})

        case2 = CaseSubscriptions(subscriptions={'sub7': sub7, 'sub8': sub8})

        set_subscriptions({'case1': CaseSubscriptions(), 'case2': case2})

        add1 = {"ancestry-0": "sub8",
                "ancestry-1": "add1",
                "events-0": "a",
                "events-1": "b"}

        add2 = {"ancestry-0": "sub7",
                "ancestry-1": "add2",
                "events-0": "c",
                "events-1": "d",
                "events-2": "e"}

        add3 = {"ancestry-0": "add3",
                "events-0": "e"}

        tree = {'sub7': {'sub4': {'sub1': {},
                                  'sub2': {}}},
                'sub8': {'sub5': {'sub3': {}},
                         'sub6': {}}}

        expected_cases_json = {'case2': construct_case_json(tree), 'case1': CaseSubscriptions().as_json()}

        response = self.app.post('/cases/subscriptions/case2/subscription/add', data=add1, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['sub8']['subscriptions']['add1'] = \
            {'events': ['a', 'b'],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)

        response = self.app.post('/cases/subscriptions/case2/subscription/add', data=add2, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['sub7']['subscriptions']['add2'] = \
            {'events': ['c', 'd', 'e'],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)

        response = self.app.post('/cases/subscriptions/case2/subscription/add', data=add3, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['add3'] = \
            {'events': ['e'],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)

    def test_add_subscription_invalid_case(self):
        sub1 = Subscription()
        sub2 = Subscription()
        sub3 = Subscription()

        sub4 = Subscription(subscriptions={'sub1': sub1, 'sub2': sub2})
        sub5 = Subscription(subscriptions={'sub3': sub3})
        sub6 = Subscription()

        sub7 = Subscription(subscriptions={'sub4': sub4})
        sub8 = Subscription(subscriptions={'sub5': sub5, 'sub6': sub6})

        case2 = CaseSubscriptions(subscriptions={'sub7': sub7, 'sub8': sub8})

        set_subscriptions({'case1': CaseSubscriptions(), 'case2': case2})

        tree = {'sub7': {'sub4': {'sub1': {},
                                  'sub2': {}}},
                'sub8': {'sub5': {'sub3': {}},
                         'sub6': {}}}

        add1 = {"ancestry-0": "sub8",
                "ancestry-1": "add1",
                "events-0": "a",
                "events-1": "b"}

        expected_cases_json = {'case2': construct_case_json(tree), 'case1': CaseSubscriptions().as_json()}
        response = self.app.post('/cases/subscriptions/junkcase/subscription/add', data=add1, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)

    def test_remove_subscription(self):
        sub1 = Subscription()
        sub2 = Subscription()
        sub3 = Subscription()

        sub4 = Subscription(subscriptions={'sub1': sub1, 'sub2': sub2})
        sub5 = Subscription(subscriptions={'sub3': sub3})
        sub6 = Subscription()

        sub7 = Subscription(subscriptions={'sub4': sub4})
        sub8 = Subscription(subscriptions={'sub5': sub5})
        sub9 = Subscription(subscriptions={'sub6': sub6})
        sub10 = Subscription()

        sub11 = Subscription(subscriptions={'sub7': sub7, 'sub8': sub8})
        sub12 = Subscription(subscriptions={'sub9': sub9})
        sub13 = Subscription(subscriptions={'sub10': sub10})

        sub14 = Subscription(subscriptions={'sub11': sub11, 'sub12': sub12, 'sub13': sub13})

        case1 = CaseSubscriptions(subscriptions={'sub14': sub14})

        sub15 = Subscription()
        sub16 = Subscription()
        sub17 = Subscription()

        sub18 = Subscription(subscriptions={'sub15': sub15, 'sub16': sub16})
        sub19 = Subscription(subscriptions={'sub17': sub17})
        sub20 = Subscription()

        sub21 = Subscription(subscriptions={'sub18': sub18})
        sub22 = Subscription(subscriptions={'sub19': sub19, 'sub20': sub20})

        case2 = CaseSubscriptions(subscriptions={'sub21': sub21, 'sub22': sub22})

        set_subscriptions({'case1': case1, 'case2': case2})

        tree1 = {'sub14': {'sub11': {'sub7': {'sub4': {'sub1': {},
                                                       'sub2': {}}},
                                     'sub8': {'sub5': {'sub3': {}}}},
                           'sub12': {'sub9': {'sub6': {}}},
                           'sub13': {'sub10': {}}}}

        tree2 = {'sub21': {'sub18': {'sub15': {},
                                     'sub16': {}}},
                 'sub22': {'sub19': {'sub17': {}},
                           'sub20': {}}}

        # test that construct expected json is working
        self.assertDictEqual({'case1': construct_case_json(tree1), 'case2': construct_case_json(tree2)},
                             subscriptions_as_json())

        def test_removal(case, ancestry, expected_tree_1, expected_tree_2):
            post_data = {"ancestry-{0}".format(i): sub for i, sub in enumerate(ancestry)}
            response = self.app.post('/cases/subscriptions/{0}/subscription/delete'.format(case),
                                     data=post_data,
                                     headers=self.headers)
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            expected_response = {'case1': construct_case_json(expected_tree_1),
                                 'case2': construct_case_json(expected_tree_2)}
            self.assertDictEqual(response, expected_response)

        tree1_after_rem10 = {'sub14': {'sub11': {'sub7': {'sub4': {'sub1': {},
                                                                   'sub2': {}}},
                                                 'sub8': {'sub5': {'sub3': {}}}},
                                       'sub12': {'sub9': {'sub6': {}}},
                                       'sub13': {}}}

        test_removal('case1', ["sub14", "sub13", "sub10"], tree1_after_rem10, tree2)

        tree2_after_rem20 = {'sub21': {'sub18': {'sub15': {},
                                                 'sub16': {}}},
                             'sub22': {'sub19': {'sub17': {}}}}
        test_removal('case2', ["sub22", "sub20"], tree1_after_rem10, tree2_after_rem20)

        tree1_after_rem9 = {'sub14': {'sub11': {'sub7': {'sub4': {'sub1': {},
                                                                  'sub2': {}}},
                                                'sub8': {'sub5': {'sub3': {}}}},
                                      'sub12': {},
                                      'sub13': {}}}
        test_removal('case1', ["sub14", "sub12", "sub9"], tree1_after_rem9, tree2_after_rem20)

        tree1_after_rem4 = {'sub14': {'sub11': {'sub7': {},
                                                'sub8': {'sub5': {'sub3': {}}}},
                                      'sub12': {},
                                      'sub13': {}}}
        test_removal('case1', ['sub14', 'sub11', 'sub7', 'sub4'], tree1_after_rem4, tree2_after_rem20)

        tree2_after_rem18 = {'sub21': {},
                             'sub22': {'sub19': {'sub17': {}}}}
        test_removal('case2', ['sub21', 'sub18'], tree1_after_rem4, tree2_after_rem18)

        tree1_after_rem11 = {'sub14': {'sub12': {},
                                       'sub13': {}}}
        test_removal('case1', ['sub14', 'sub11'], tree1_after_rem11, tree2_after_rem18)

        tree1_after_rem14 = {}
        test_removal('case1', ['sub14'], tree1_after_rem14, tree2_after_rem18)

        tree2_after_rem22 = {'sub21': {}}
        test_removal('case2', ['sub22'], tree1_after_rem14, tree2_after_rem22)

        tree2_after_rem21 = {}
        test_removal('case2', ['sub21'], tree1_after_rem14, tree2_after_rem21)

    def test_remove_subscription_invalid_case(self):
        data = {"ancestry-0": "sub1"}
        set_subscriptions({'case1': CaseSubscriptions(), 'case2': CaseSubscriptions()})
        expected_cases_json = {'case2': CaseSubscriptions().as_json(), 'case1': CaseSubscriptions().as_json()}
        response = self.app.post('/cases/subscriptions/junkcase/subscription/delete', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)

    def test_remove_subscription_invalid_ancestry(self):
        sub15 = Subscription()
        sub16 = Subscription()
        sub17 = Subscription()

        sub18 = Subscription(subscriptions={'sub15': sub15, 'sub16': sub16})
        sub19 = Subscription(subscriptions={'sub17': sub17})
        sub20 = Subscription()

        sub21 = Subscription(subscriptions={'sub18': sub18})
        sub22 = Subscription(subscriptions={'sub19': sub19, 'sub20': sub20})

        case2 = CaseSubscriptions(subscriptions={'sub21': sub21, 'sub22': sub22})

        set_subscriptions({'case1': CaseSubscriptions(), 'case2': case2})

        tree2 = {'sub21': {'sub18': {'sub15': {},
                                     'sub16': {}}},
                 'sub22': {'sub19': {'sub17': {}},
                           'sub20': {}}}

        expected_cases_json = {'case1': CaseSubscriptions().as_json(), 'case2': construct_case_json(tree2)}

        def test_junk_path(case, path):
            data = {"ancestry-{0}".format(i): sub for i, sub in enumerate(path)}
            response = self.app.post('/cases/subscriptions/{0}/subscription/delete'.format(case),
                                     data=data, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            self.assertDictEqual(response, expected_cases_json)

        test_junk_path('case2', ["sub21", "sub18", "sub15", "sub20"])
        test_junk_path('case2', ["sub1"])
        test_junk_path('case1', ['sub21'])
        test_junk_path('case2', ["sub22", "sub20", "sub17"])

    def test_edit_event_note(self):
        case1, _ = construct_case1()
        case2, _ = construct_case2()
        case3, _ = construct_case1()
        case4, _ = construct_case2()
        cases = {'case1': case1, 'case2': case2, 'case3': case3, 'case4': case4}
        set_subscriptions(cases)

        elem1 = ExecutionElement(name='b', parent_name='a')
        elem2 = ExecutionElement(name='c', parent_name='b', ancestry=['a', 'b', 'c'])
        elem3 = ExecutionElement(name='d', parent_name='c')
        elem4 = ExecutionElement()

        event1 = _EventEntry(elem1, 'message1', 'SYSTEM')
        event2 = _EventEntry(elem2, 'message2', 'WORKFLOW')
        event3 = _EventEntry(elem3, 'message3', 'STEP')
        event4 = _EventEntry(elem4, 'message4', 'NEXT')

        case_database.case_db.add_event(event=event1, cases=['case1', 'case3'])
        case_database.case_db.add_event(event=event2, cases=['case2', 'case4'])
        case_database.case_db.add_event(event=event3, cases=['case2', 'case3', 'case4'])
        case_database.case_db.add_event(event=event4, cases=['case1'])

        events = case_database.case_db.session.query(case_database.Event).all()
        smallest_id = min([event.id for event in events])
        altered_event = [event for event in events if event.id == smallest_id]
        expected_event = altered_event[0].as_json()
        expected_event['note'] = 'Note1'

        data = {"note": 'Note1'}
        response = self.app.post('/cases/event/{0}/edit'.format(smallest_id), data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_event)

        expected_event['note'] = 'Note2'

        data = {"note": 'Note2'}
        response = self.app.post('/cases/event/{0}/edit'.format(smallest_id), data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_event)

    def test_edit_event_note_invalid_event_id(self):
        case1, _ = construct_case1()
        case2, _ = construct_case2()
        case3, _ = construct_case1()
        case4, _ = construct_case2()
        cases = {'case1': case1, 'case2': case2, 'case3': case3, 'case4': case4}
        set_subscriptions(cases)

        elem1 = ExecutionElement(name='b', parent_name='a')
        elem2 = ExecutionElement(name='c', parent_name='b', ancestry=['a', 'b', 'c'])
        elem3 = ExecutionElement(name='d', parent_name='c')
        elem4 = ExecutionElement()

        event1 = _EventEntry(elem1, 'message1', 'SYSTEM')
        event2 = _EventEntry(elem2, 'message2', 'WORKFLOW')
        event3 = _EventEntry(elem3, 'message3', 'STEP')
        event4 = _EventEntry(elem4, 'message4', 'NEXT')

        case_database.case_db.add_event(event=event1, cases=['case1', 'case3'])
        case_database.case_db.add_event(event=event2, cases=['case2', 'case4'])
        case_database.case_db.add_event(event=event3, cases=['case2', 'case3', 'case4'])
        case_database.case_db.add_event(event=event4, cases=['case1'])

        events = case_database.case_db.session.query(case_database.Event).all()
        invalid_id = max([event.id for event in events]) + 1

        data = {"note": 'Note2'}
        response = self.app.post('/cases/event/{0}/edit'.format(invalid_id), data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {"status": "invalid event"})

