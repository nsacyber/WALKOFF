import json
import os

import tests.config
from tests.util.case import construct_case1, construct_case2, construct_case_json
import core.case.database as case_database
from core.case.subscription import set_subscriptions, clear_subscriptions, CaseSubscriptions, \
    GlobalSubscriptions, subscriptions_as_json, Subscription, delete_cases, add_cases
from core.executionelement import ExecutionElement
from core.case.callbacks import _EventEntry
import core.config.paths
from os.path import join
from tests.util.servertestcase import ServerTestCase
from server.blueprints.cases import convert_ancestry
from core.helpers import construct_workflow_name_key


class TestCaseServer(ServerTestCase):
    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tear_down()
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
        response = self.app.get('/cases/', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases = set(cases.keys())
        received_cases = [case['name'] for case in response['cases']]
        self.assertEqual(len(expected_cases), len(received_cases), 'Received unexpected number of cases')
        self.assertSetEqual(expected_cases, set(received_cases), 'Received incorrect cases')

    def test_display_cases_none(self):
        response = self.app.get('/cases/', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases = []
        received_cases = [case['name'] for case in response['cases']]
        self.assertEqual(len(expected_cases), len(received_cases), 'Received unexpected number of cases')
        self.assertSetEqual(set(expected_cases), set(received_cases), 'Received incorrect cases')

    def test_display_case_not_found(self):
        response = self.get_with_status_check('/cases/hiThere', 'Case with given name does not exist',
                                              headers=self.headers)
        with self.assertRaises(KeyError):
            _ = response['cases']

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

    def test_export_cases_no_filename(self):
        TestCaseServer.__basic_case_setup()
        expected_subs = subscriptions_as_json()
        self.post_with_status_check('/cases/export', 'success', headers=self.headers)
        self.assertIn('cases.json', os.listdir(tests.config.test_data_path))
        with open(core.config.paths.default_case_export_path, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            read_json = json.loads(read_file)
        self.assertDictEqual(read_json, expected_subs)

    def test_export_cases_with_filename(self):
        TestCaseServer.__basic_case_setup()
        expected_subs = subscriptions_as_json()
        filename = os.path.join(tests.config.test_data_path, 'case_other.json')
        data = {"filename": filename}
        self.post_with_status_check('/cases/export', 'success', headers=self.headers, data=data)
        self.assertIn('case_other.json', os.listdir(tests.config.test_data_path))
        with open(filename, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            read_json = json.loads(read_file)
        self.assertDictEqual(read_json, expected_subs)

    def test_import_cases_no_filename(self):
        TestCaseServer.__basic_case_setup()
        self.post_with_status_check('/cases/export', 'success', headers=self.headers)
        # essentially add two more cases, swap contents of case 1 and 2 in case_subscriptions
        case1, _ = construct_case2()
        case2, _ = construct_case1()
        case5, _ = construct_case1()
        case6, _ = construct_case2()
        delete_cases(['case1' 'case2'])
        cases = {'case1': case1, 'case2': case2, 'case5': case5, 'case6': case6}
        add_cases(cases)
        response = self.get_with_status_check('/cases/import', 'success', headers=self.headers)
        expected_json = {'case1': construct_case1()[0],
                         'case2': construct_case2()[0],
                         'case3': construct_case1()[0],
                         'case4': construct_case2()[0],
                         'case5': construct_case1()[0],
                         'case6': construct_case2()[0]}
        expected_json = {key: value.as_json() for key, value in expected_json.items()}
        self.assertDictEqual(subscriptions_as_json(), expected_json)
        self.assertIn('cases', response)
        self.assertDictEqual(response['cases'], expected_json)

    def test_import_cases_with_filename(self):
        TestCaseServer.__basic_case_setup()
        filename = os.path.join(tests.config.test_data_path, 'case_other.json')
        data = {"filename": filename}
        self.post_with_status_check('/cases/export', 'success', headers=self.headers, data=data)
        # essentially add two more cases, swap contents of case 1 and 2 in case_subscriptions
        case1, _ = construct_case2()
        case2, _ = construct_case1()
        case5, _ = construct_case1()
        case6, _ = construct_case2()
        delete_cases(['case1' 'case2'])
        cases = {'case1': case1, 'case2': case2, 'case5': case5, 'case6': case6}
        add_cases(cases)
        response = self.get_with_status_check('/cases/import', 'success', headers=self.headers, data=data)
        expected_json = {'case1': construct_case1()[0],
                         'case2': construct_case2()[0],
                         'case3': construct_case1()[0],
                         'case4': construct_case2()[0],
                         'case5': construct_case1()[0],
                         'case6': construct_case2()[0]}
        expected_json = {key: value.as_json() for key, value in expected_json.items()}
        self.assertDictEqual(subscriptions_as_json(), expected_json)
        self.assertIn('cases', response)
        self.assertDictEqual(response['cases'], expected_json)

    def test_crud_case_invalid_action(self):
        self.post_with_status_check('/cases/case3/junk', 'Invalid operation junk', headers=self.headers)

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
        self.post_with_status_check('/cases/subscriptions/case1/global/edit', 'Error: Case name case1 was not found',
                                    data=global_subs, headers=self.headers)

        case2 = CaseSubscriptions()
        set_subscriptions({'case2': case2})
        self.post_with_status_check('/cases/subscriptions/case1/global/edit', 'Error: Case name case1 was not found',
                                    data=global_subs, headers=self.headers)

    def test_convert_ancestry(self):
        input_output = [(['a'], ['a']),
                        (['a', 'b'], ['a', 'b']),
                        (['a', 'b', 'c'], ['a', construct_workflow_name_key('b', 'c')]),
                        (['a', 'b', 'c', 'd'], ['a', construct_workflow_name_key('b', 'c'), 'd'])]
        for input_ancestry, output_ancestry in input_output:
            self.assertListEqual(convert_ancestry(input_ancestry), output_ancestry)

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

        add1 = {"ancestry": ["sub8", "add1"],
                "events": ["a", "b"]}

        add2 = {"ancestry": ["sub7", "add2"],
                "events": ["c", "d", "e"]}

        add3 = {"ancestry": ["add3"],
                "events": ["e"]}

        tree = {'sub7': {'sub4': {'sub1': {},
                                  'sub2': {}}},
                'sub8': {'sub5': {'sub3': {}},
                         'sub6': {}}}

        expected_cases_json = {'case2': construct_case_json(tree), 'case1': CaseSubscriptions().as_json()}

        response = self.app.post('/cases/subscriptions/case2/subscription/add',
                                 data=json.dumps(add1),
                                 headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['sub8']['subscriptions']['add1'] = \
            {'events': ['a', 'b'],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)

        response = self.app.post('/cases/subscriptions/case2/subscription/add',
                                 data=json.dumps(add2),
                                 headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['sub7']['subscriptions']['add2'] = \
            {'events': ['c', 'd', 'e'],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)

        response = self.app.post('/cases/subscriptions/case2/subscription/add',
                                 data=json.dumps(add3),
                                 headers=self.headers,
                                 content_type='application/json')
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

        add1 = {"ancestry": ["sub8", "add1"],
                "events": ["a", "b"]}

        expected_cases_json = {'case2': construct_case_json(tree), 'case1': CaseSubscriptions().as_json()}
        response = self.app.post('/cases/subscriptions/junkcase/subscription/add',
                                 data=json.dumps(add1),
                                 headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)

    def test_add_subscription_no_json(self):
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

        add1 = {"ancestry": ["sub8", "add1"],
                "events": ["a", "b"]}

        self.post_with_status_check('/cases/subscriptions/case1/subscription/add',
                                    'Error: no JSON in request',
                                    data=add1,
                                    headers=self.headers,
                                    content_type='application/json')

    def test_add_subscription_malformed_json(self):
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

        bad1 = {"ancestry_bad": ["sub8", "add1"],
                "events": ["a", "b"]}
        bad3 = {"ancestry_bad": ["sub8", "add1"],
                "events_bad": ["a", "b"]}

        for bad_json in [bad1, bad3]:
            self.post_with_status_check('/cases/subscriptions/case1/subscription/add',
                                        'Error: malformed JSON',
                                        data=json.dumps(bad_json),
                                        headers=self.headers,
                                        content_type='application/json')

    def test_edit_subscription(self):
        sub1 = Subscription()
        sub2 = Subscription()
        sub3 = Subscription()

        sub4 = Subscription(subscriptions={'sub1': sub1, 'sub2': sub2})
        sub5 = Subscription(subscriptions={'sub3': sub3})
        sub6 = Subscription()

        sub7 = Subscription(subscriptions={'sub4': sub4})
        sub5_name = construct_workflow_name_key('playbook', 'sub5')
        sub8 = Subscription(subscriptions={sub5_name: sub5, 'sub6': sub6})

        case2 = CaseSubscriptions(subscriptions={'sub7': sub7, 'sub8': sub8})

        set_subscriptions({'case1': CaseSubscriptions(), 'case2': case2})

        edit1 = {"ancestry": ["sub8", "playbook", "sub5", "sub3"],
                 "events": ["a", "b"]}

        edit2 = {"ancestry": ["sub7", "sub4"],
                 "events": ["c", "d", "e"]}

        edit3 = {"ancestry": ["sub8"],
                 "events": ["e"]}

        tree = {'sub7': {'sub4': {'sub1': {},
                                  'sub2': {}}},
                'sub8': {sub5_name: {'sub3': {}},
                         'sub6': {}}}

        expected_cases_json = {'case2': construct_case_json(tree), 'case1': CaseSubscriptions().as_json()}
        expected_cases_json['case2']['subscriptions']['sub8']['subscriptions'][sub5_name]['subscriptions']['sub3'][
            'events'] \
            = ['a', 'b']

        response = self.app.post('/cases/subscriptions/case2/subscription/edit',
                                 data=json.dumps(edit1),
                                 headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)

        expected_cases_json['case2']['subscriptions']['sub7']['subscriptions']['sub4']['events'] \
            = ['c', 'd', 'e']

        response = self.app.post('/cases/subscriptions/case2/subscription/edit',
                                 data=json.dumps(edit2),
                                 headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)

        expected_cases_json['case2']['subscriptions']['sub8']['events'] = ['e']

        response = self.app.post('/cases/subscriptions/case2/subscription/edit',
                                 data=json.dumps(edit3),
                                 headers=self.headers,
                                 content_type='application/json')
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

        edit1 = {"ancestry": ["sub8", "sub5", "junk"],
                 "events": ["a", "b"]}
        self.post_with_status_check('/cases/subscriptions/case2/subscription/edit',
                                    'Error occurred while editing subscription',
                                    data=json.dumps(edit1),
                                    headers=self.headers,
                                    content_type='application/json')

    def test_edit_subscription_invalid_case(self):
        edit = {"ancestry": [], "events": []}
        self.post_with_status_check('/cases/subscriptions/case1/subscription/edit',
                                    'Error occurred while editing subscription',
                                    data=json.dumps(edit),
                                    headers=self.headers,
                                    content_type='application/json')

    def test_edit_subscription_no_json(self):
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

        edit1 = {"ancestry": ["sub8", "sub5", "junk"],
                 "events": ["a", "b"]}
        self.post_with_status_check('/cases/subscriptions/case2/subscription/edit',
                                    'Error: no JSON in request',
                                    data=edit1,
                                    headers=self.headers,
                                    content_type='application/json')

    def test_edit_subscriptions_invalid_json(self):
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

        edit1 = {"ancestry_bad": ["sub8", "sub5", "junk"],
                 "events": ["a", "b"]}
        edit2 = {"ancestry": ["sub8", "sub5", "junk"],
                 "events_bad": ["a", "b"]}
        edit3 = {"ancestry_bad": ["sub8", "sub5", "junk"],
                 "events_bad": ["a", "b"]}

        for edit in [edit1, edit2, edit3]:
            self.post_with_status_check('/cases/subscriptions/case2/subscription/edit',
                                        'Error: malformed JSON',
                                        data=json.dumps(edit),
                                        headers=self.headers,
                                        content_type='application/json')

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

        sub11_name = construct_workflow_name_key('playbook', 'sub11')
        sub12_name = construct_workflow_name_key('playbook', 'sub12')
        sub13_name = construct_workflow_name_key('playbook', 'sub13')
        sub14 = Subscription(subscriptions={sub11_name: sub11, sub12_name: sub12, sub13_name: sub13})

        case1 = CaseSubscriptions(subscriptions={'sub14': sub14})

        sub15 = Subscription()
        sub16 = Subscription()
        sub17 = Subscription()

        sub18 = Subscription(subscriptions={'sub15': sub15, 'sub16': sub16})
        sub19 = Subscription(subscriptions={'sub17': sub17})
        sub20 = Subscription()

        sub18_name = construct_workflow_name_key('playbook', 'sub18')
        sub19_name = construct_workflow_name_key('playbook', 'sub19')
        sub20_name = construct_workflow_name_key('playbook', 'sub20')
        sub21 = Subscription(subscriptions={sub18_name: sub18})
        sub22 = Subscription(subscriptions={sub19_name: sub19, sub20_name: sub20})

        case2 = CaseSubscriptions(subscriptions={'sub21': sub21, 'sub22': sub22})

        set_subscriptions({'case1': case1, 'case2': case2})

        tree1 = {'sub14': {sub11_name: {'sub7': {'sub4': {'sub1': {},
                                                          'sub2': {}}},
                                        'sub8': {'sub5': {'sub3': {}}}},
                           sub12_name: {'sub9': {'sub6': {}}},
                           sub13_name: {'sub10': {}}}}

        tree2 = {'sub21': {sub18_name: {'sub15': {},
                                        'sub16': {}}},
                 'sub22': {sub19_name: {'sub17': {}},
                           sub20_name: {}}}

        # test that construct expected json is working
        self.assertDictEqual({'case1': construct_case_json(tree1), 'case2': construct_case_json(tree2)},
                             subscriptions_as_json())

        def test_removal(case, ancestry, expected_tree_1, expected_tree_2):
            post_data = {"ancestry": ancestry}
            response = self.app.post('/cases/subscriptions/{0}/subscription/delete'.format(case),
                                     data=json.dumps(post_data),
                                     headers=self.headers,
                                     content_type='application/json')
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            expected_response = {'case1': construct_case_json(expected_tree_1),
                                 'case2': construct_case_json(expected_tree_2)}
            self.assertDictEqual(response, expected_response)

        tree1_after_rem10 = {'sub14': {sub11_name: {'sub7': {'sub4': {'sub1': {},
                                                                      'sub2': {}}},
                                                    'sub8': {'sub5': {'sub3': {}}}},
                                       sub12_name: {'sub9': {'sub6': {}}},
                                       sub13_name: {}}}

        test_removal('case1', ["sub14", "playbook", "sub13", "sub10"], tree1_after_rem10, tree2)

        tree2_after_rem20 = {'sub21': {sub18_name: {'sub15': {},
                                                    'sub16': {}}},
                             'sub22': {sub19_name: {'sub17': {}}}}
        test_removal('case2', ["sub22", 'playbook', "sub20"], tree1_after_rem10, tree2_after_rem20)

        tree1_after_rem9 = {'sub14': {sub11_name: {'sub7': {'sub4': {'sub1': {},
                                                                     'sub2': {}}},
                                                   'sub8': {'sub5': {'sub3': {}}}},
                                      sub12_name: {},
                                      sub13_name: {}}}
        test_removal('case1', ["sub14", "playbook", "sub12", "sub9"], tree1_after_rem9, tree2_after_rem20)

        tree1_after_rem4 = {'sub14': {sub11_name: {'sub7': {},
                                                   'sub8': {'sub5': {'sub3': {}}}},
                                      sub12_name: {},
                                      sub13_name: {}}}
        test_removal('case1', ['sub14', 'playbook', 'sub11', 'sub7', 'sub4'], tree1_after_rem4, tree2_after_rem20)

        tree2_after_rem18 = {'sub21': {},
                             'sub22': {sub19_name: {'sub17': {}}}}
        test_removal('case2', ['sub21', 'playbook', 'sub18'], tree1_after_rem4, tree2_after_rem18)

        tree1_after_rem11 = {'sub14': {sub12_name: {},
                                       sub13_name: {}}}
        test_removal('case1', ['sub14', 'playbook', 'sub11'], tree1_after_rem11, tree2_after_rem18)

        tree1_after_rem14 = {}
        test_removal('case1', ['sub14'], tree1_after_rem14, tree2_after_rem18)

        tree2_after_rem22 = {'sub21': {}}
        test_removal('case2', ['sub22'], tree1_after_rem14, tree2_after_rem22)

        tree2_after_rem21 = {}
        test_removal('case2', ['sub21'], tree1_after_rem14, tree2_after_rem21)

    def test_remove_subscription_invalid_case(self):
        data = {"ancestry": ["sub1"]}
        set_subscriptions({'case1': CaseSubscriptions(), 'case2': CaseSubscriptions()})
        expected_cases_json = {'case2': CaseSubscriptions().as_json(), 'case1': CaseSubscriptions().as_json()}
        response = self.app.post('/cases/subscriptions/junkcase/subscription/delete',
                                 data=json.dumps(data),
                                 headers=self.headers,
                                 content_type='application/json')
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
            data = {"ancestry": path}
            response = self.app.post('/cases/subscriptions/{0}/subscription/delete'.format(case),
                                     data=json.dumps(data),
                                     headers=self.headers,
                                     content_type='application/json')
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            self.assertDictEqual(response, expected_cases_json)

        test_junk_path('case2', ["sub21", "sub18", "sub15", "sub20"])
        test_junk_path('case2', ["sub1"])
        test_junk_path('case1', ['sub21'])
        test_junk_path('case2', ["sub22", "sub20", "sub17"])

    def test_remove_subscription_no_json(self):
        data = {"ancestry": ["sub1"]}
        set_subscriptions({'case1': CaseSubscriptions(), 'case2': CaseSubscriptions()})
        self.post_with_status_check('/cases/subscriptions/junkcase/subscription/delete',
                                    'Error: no JSON in request',
                                    data=data,
                                    headers=self.headers,
                                    content_type='application/json')

    def test_remove_subscription_invalid_json(self):
        data = {"ancestry_bad": ["sub1"]}
        set_subscriptions({'case1': CaseSubscriptions(), 'case2': CaseSubscriptions()})
        self.post_with_status_check('/cases/subscriptions/junkcase/subscription/delete',
                                    'Error: malformed JSON',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json')

    def test_invalid_subscription_action(self):
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
        self.post_with_status_check('/cases/subscriptions/case1/subscription/junkAction',
                                    'error: unknown subscription action',
                                    headers=self.headers)

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
        self.post_with_status_check('/cases/event/{0}/edit'.format(invalid_id), 'invalid event',
                                    data=data, headers=self.headers)
