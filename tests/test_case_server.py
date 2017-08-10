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
from server.endpoints.cases import convert_ancestry, convert_scheduler_events
from core.helpers import construct_workflow_name_key
from tests.util.assertwrappers import orderless_list_compare
import server.flaskserver as server
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from server.return_codes import *
from collections import OrderedDict


class TestCaseServer(ServerTestCase):
    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tear_down()
        clear_subscriptions()
        for case in server.running_context.CaseSubscription.query.all():
            server.running_context.db.session.delete(case)
        server.running_context.db.session.commit()

    @staticmethod
    def __basic_case_setup():
        case1, _ = construct_case1()
        case2, _ = construct_case2()
        case3, _ = construct_case1()
        case4, _ = construct_case2()
        cases = {'case1': case1, 'case2': case2, 'case3': case3, 'case4': case4}
        set_subscriptions(cases)
        return cases

    def test_add_case_no_existing_cases(self):
        data = {'name': 'case1', 'note': 'Test'}
        response = self.put_with_status_check('/api/cases', headers=self.headers, data=json.dumps(data),
                                              content_type='application/json', status_code=OBJECT_CREATED)
        self.assertEqual(response, {'id': 1, 'name': 'case1', 'note': 'Test', 'subscriptions': {}})
        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = server.running_context.CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        case = cases_config[0]
        self.assertEqual(case.name, 'case1')
        self.assertEqual(case.subscriptions, '{}')

    def test_add_case_existing_cases(self):
        case1 = CaseSubscriptions()
        set_subscriptions({'case1': case1})
        response = self.put_with_status_check('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                                              status_code=OBJECT_CREATED, content_type='application/json')
        self.assertEqual(response, {'id': 1, 'name': 'case2', 'note': '', 'subscriptions': {}})
        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1', 'case2']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = server.running_context.CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case2'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, '{}')

    def test_add_case_duplicate_case_out_of_sync(self):
        global_subs = GlobalSubscriptions(controller=['a'])
        case1 = CaseSubscriptions(global_subscriptions=global_subs)
        set_subscriptions({'case1': case1})
        expected_json = {'id': 1, 'name': 'case1', 'note': '', 'subscriptions': {}}
        response = self.put_with_status_check('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                                              status_code=OBJECT_CREATED, content_type='application/json')
        self.assertEqual(response, expected_json)

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = server.running_context.CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case1'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, '{}')

    def test_add_case_duplicate_case_in_sync(self):
        global_subs = GlobalSubscriptions(controller=['a'])
        case1 = CaseSubscriptions(global_subscriptions=global_subs)
        set_subscriptions({'case1': case1})
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}), content_type='application/json')
        self.put_with_status_check('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                                   status_code=OBJECT_EXISTS_ERROR, content_type='application/json')

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = server.running_context.CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case1'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, '{}')

    def test_display_cases_typical(self):
        response = json.loads(self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                              content_type='application/json').get_data(as_text=True))
        case1_id = response['id']
        response = json.loads(self.app.put('api/cases', headers=self.headers,
                                           data=json.dumps({'name': 'case2', "note": 'note1'}),
                                           content_type='application/json').get_data(as_text=True))
        case2_id = response['id']

        response = json.loads(self.app.put('api/cases', headers=self.headers,
                                           data=json.dumps({'name': 'case3', "note": 'note2'}),
                                           content_type='application/json').get_data(as_text=True))
        case3_id = response['id']
        response = self.get_with_status_check('/api/cases', headers=self.headers)
        expected_response = [{'note': '', 'subscriptions': {}, 'id': case1_id, 'name': 'case1'},
                             {'note': 'note1', 'subscriptions': {}, 'id': case2_id, 'name': 'case2'},
                             {'note': 'note2', 'subscriptions': {}, 'id': case3_id, 'name': 'case3'}]
        for case in response:
            self.assertIn(case, expected_response)

    def test_display_cases_none(self):
        response = self.get_with_status_check('/api/cases', headers=self.headers)
        self.assertListEqual(response, [])

    def test_display_case_not_found(self):
        self.get_with_status_check('/api/cases/404',
                                   error='Case does not exist.',
                                   headers=self.headers,
                                   status_code=OBJECT_DNE_ERROR)

    def test_delete_case_only_case(self):
        response = json.loads(self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json').get_data(as_text=True))
        case_id = response['id']
        response = self.delete_with_status_check('api/cases/{0}'.format(case_id), headers=self.headers,
                                                status_code=SUCCESS)
        self.assertEqual(response, {})

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = []
        orderless_list_compare(self, cases, expected_cases)
        cases_config = server.running_context.CaseSubscription.query.all()
        self.assertListEqual(cases_config, [])

    def test_delete_case(self):
        response = json.loads(self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json').get_data(as_text=True))
        case1_id = response['id']
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type='application/json')
        self.delete_with_status_check('api/cases/{0}'.format(case1_id), headers=self.headers, status_code=SUCCESS)

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case2']
        orderless_list_compare(self, cases, expected_cases)

        cases_config = server.running_context.CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)

        self.assertEqual(cases_config[0].name, 'case2')
        self.assertEqual(cases_config[0].subscriptions, '{}')

    def test_delete_case_invalid_case(self):
        case1 = CaseSubscriptions()
        case2 = CaseSubscriptions()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type='application/json')
        self.delete_with_status_check('api/cases/3',
                                      error='Case does not exist.',
                                      headers=self.headers,
                                      status_code=OBJECT_DNE_ERROR)

        db_cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = list(cases.keys())
        orderless_list_compare(self, db_cases, expected_cases)

        cases_config = server.running_context.CaseSubscription.query.all()
        orderless_list_compare(self, [case.name for case in cases_config], ['case1', 'case2'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, '{}')

    def test_delete_case_no_cases(self):
        self.delete_with_status_check('api/cases/404',
                                      error='Case does not exist.',
                                      headers=self.headers,
                                      status_code=OBJECT_DNE_ERROR)

        db_cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = []
        orderless_list_compare(self, db_cases, expected_cases)

        cases_config = server.running_context.CaseSubscription.query.all()
        self.assertListEqual(cases_config, [])

    def test_edit_case(self):
        response = json.loads(self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json').get_data(as_text=True))
        case1_id = response['id']
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type='application/json')
        data = {"name": "renamed",
                "note": "note1",
                "id": case1_id}
        response = self.post_with_status_check('api/cases', data=json.dumps(data), headers=self.headers,
                                               content_type='application/json', status_code=SUCCESS)

        self.assertDictEqual(response, {'note': 'note1', 'subscriptions': {}, 'id': 1, 'name': 'renamed'})

        result_cases = case_database.case_db.cases_as_json()
        case1_new_json = next((case for case in result_cases if case['name'] == "renamed"), None)
        self.assertIsNotNone(case1_new_json)
        self.assertDictEqual(case1_new_json, {'id': 1, 'name': 'renamed'})

    def test_edit_case_no_name(self):
        response = json.loads(self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type='application/json').get_data(as_text=True))
        case2_id = response['id']
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        data = {"note": "note1", "id": case2_id}
        response = self.post_with_status_check('api/cases', data=json.dumps(data), headers=self.headers,
                                 content_type='application/json', status_code=SUCCESS)
        self.assertDictEqual(response, {'note': 'note1', 'subscriptions': {}, 'id': 1, 'name': 'case2'})

    def test_edit_case_no_note(self):
        response = json.loads(self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                                           content_type='application/json').get_data(as_text=True))
        case1_id = response['id']
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type='application/json')
        data = {"name": "renamed", "id": case1_id}
        response = self.post_with_status_check('api/cases', data=json.dumps(data), headers=self.headers,
                                 content_type='application/json', status_code=SUCCESS)
        self.assertDictEqual(response, {'note': '', 'subscriptions': {}, 'id': 1, 'name': 'renamed'})

    def test_edit_case_invalid_case(self):
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type = 'application/json')
        data = {"name": "renamed", "id": 404}
        self.post_with_status_check('api/cases',
                                    error='Case does not exist.',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=OBJECT_DNE_ERROR)

    def test_export_cases_no_filename(self):
        TestCaseServer.__basic_case_setup()
        expected_subs = subscriptions_as_json()
        self.post_with_status_check('api/cases/export', headers=self.headers)
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
        self.post_with_status_check('api/cases/export', headers=self.headers, data=json.dumps(data), content_type='application/json')
        self.assertIn('case_other.json', os.listdir(tests.config.test_data_path))
        with open(filename, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            read_json = json.loads(read_file)
        self.assertDictEqual(read_json, expected_subs)

    def __assert_subscriptions_synced(self, case_name):
        cases_config = server.running_context.CaseSubscription.query.filter_by(name=case_name).all()
        self.assertEqual(len(cases_config), 1)
        case = cases_config[0]
        self.assertIn(case_name, subscriptions_as_json())
        self.assertDictEqual(json.loads(case.subscriptions), subscriptions_as_json()[case_name])

    def test_import_cases_no_filename(self):
        TestCaseServer.__basic_case_setup()
        self.post_with_status_check('api/cases/export', headers=self.headers)
        # essentially add two more cases, swap contents of case 1 and 2 in case_subscriptions
        case1, _ = construct_case2()
        case2, _ = construct_case1()
        case5, _ = construct_case1()
        case6, _ = construct_case2()
        delete_cases(['case1' 'case2'])
        cases = {'case1': case1, 'case2': case2, 'case5': case5, 'case6': case6}
        add_cases(cases)

        response = self.get_with_status_check('api/cases/import', headers=self.headers)
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
        for case in ['case1', 'case2', 'case3', 'case4']:
            self.__assert_subscriptions_synced(case)

    def test_import_cases_with_filename(self):
        TestCaseServer.__basic_case_setup()
        filename = os.path.join(tests.config.test_data_path, 'case_other.json')
        data = {"filename": filename}
        self.post_with_status_check('api/cases/export', headers=self.headers, data=json.dumps(data), content_type='application/json')
        # essentially add two more cases, swap contents of case 1 and 2 in case_subscriptions
        case1, _ = construct_case2()
        case2, _ = construct_case1()
        case5, _ = construct_case1()
        case6, _ = construct_case2()
        delete_cases(['case1' 'case2'])
        cases = {'case1': case1, 'case2': case2, 'case5': case5, 'case6': case6}
        add_cases(cases)
        response = self.get_with_status_check('api/cases/import', headers=self.headers, data=json.dumps(data), content_type='application/json')
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
        for case in ['case1', 'case2', 'case3', 'case4']:
            self.__assert_subscriptions_synced(case)

    def test_display_possible_subscriptions(self):
        with open(join('.', 'data', 'events.json')) as f:
            expected_response = json.loads(f.read(), object_pairs_hook=OrderedDict)
        expected_response = [{'type': element_type, 'events': events}
                             for element_type, events in expected_response.items()]
        response = self.app.get('/availablesubscriptions', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertListEqual(response, expected_response)

    def test_display_subscriptions(self):
        case1, accept1 = construct_case1()
        case2, accept2 = construct_case2()
        case3, accept3 = construct_case1()
        case4, accept4 = construct_case2()
        cases = {'case1': case1, 'case2': case2, 'case3': case3, 'case4': case4}
        set_subscriptions(cases)

        expected_response = {key: case.as_json() for key, case in cases.items()}

        response = self.app.get('/cases/subscriptions', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(expected_response, response)

    def test_convert_ancestry(self):
        input_output = [(['a'], ['a']),
                        (['a', 'b'], ['a', 'b']),
                        (['a', 'b', 'c'], ['a', construct_workflow_name_key('b', 'c')]),
                        (['a', 'b', 'c', 'd'], ['a', construct_workflow_name_key('b', 'c'), 'd'])]
        for input_ancestry, output_ancestry in input_output:
            self.assertListEqual(convert_ancestry(input_ancestry), output_ancestry)

    def test_convert_scheduler_events(self):
        input_output = [(["Scheduler Start", "Scheduler Shutdown", "Scheduler Paused", "Scheduler Resumed", "Job Added",
                          "Job Removed", "Job Executed", "Job Error"],
                         [EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED,
                          EVENT_SCHEDULER_RESUMED, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_JOB_EXECUTED,
                          EVENT_JOB_ERROR]),
                        ([], []),
                        (["Scheduler Start", "Scheduler Shutdown", "UnknownEvent"],
                         [EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN])]
        for input_events, output in input_output:
            orderless_list_compare(self, convert_scheduler_events(input_events), output)

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
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type = 'application/json')
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

        response = self.app.put('/cases/case2/subscriptions',
                                data=json.dumps(add1),
                                headers=self.headers,
                                content_type='application/json')
        self.assertEqual(response.status_code, OBJECT_CREATED)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['sub8']['subscriptions']['add1'] = \
            {'events': ['a', 'b'],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)
        self.__assert_subscriptions_synced('case2')

        response = self.app.put('/cases/case2/subscriptions',
                                data=json.dumps(add2),
                                headers=self.headers,
                                content_type='application/json')
        self.assertEqual(response.status_code, OBJECT_CREATED)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['sub7']['subscriptions']['add2'] = \
            {'events': ['c', 'd', 'e'],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)
        self.__assert_subscriptions_synced('case2')

        response = self.app.put('/cases/case2/subscriptions',
                                data=json.dumps(add3),
                                headers=self.headers,
                                content_type='application/json')
        self.assertEqual(response.status_code, OBJECT_CREATED)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['add3'] = \
            {'events': [],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)
        self.__assert_subscriptions_synced('case2')

    def test_add_subscription_duplicate(self):
        sub1 = Subscription()
        sub2 = Subscription()
        sub3 = Subscription()

        sub4 = Subscription(subscriptions={'sub1': sub1, 'sub2': sub2})
        sub5 = Subscription(subscriptions={'sub3': sub3})
        sub6 = Subscription()

        sub7 = Subscription(subscriptions={'sub4': sub4})
        sub8 = Subscription(subscriptions={'sub5': sub5, 'sub6': sub6})

        case2 = CaseSubscriptions(subscriptions={'sub7': sub7, 'sub8': sub8})
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type = 'application/json')
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

        response = self.app.put('/cases/case2/subscriptions',
                                data=json.dumps(add1),
                                headers=self.headers,
                                content_type='application/json')
        self.assertEqual(response.status_code, OBJECT_CREATED)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['sub8']['subscriptions']['add1'] = \
            {'events': ['a', 'b'],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)
        self.__assert_subscriptions_synced('case2')

        response = self.app.put('/cases/case2/subscriptions',
                                data=json.dumps(add2),
                                headers=self.headers,
                                content_type='application/json')
        self.assertEqual(response.status_code, OBJECT_CREATED)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['sub7']['subscriptions']['add2'] = \
            {'events': ['c', 'd', 'e'],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)
        self.__assert_subscriptions_synced('case2')

        response = self.app.put('/cases/case2/subscriptions',
                                data=json.dumps(add3),
                                headers=self.headers,
                                content_type='application/json')
        self.assertEqual(response.status_code, OBJECT_CREATED)
        response = json.loads(response.get_data(as_text=True))
        expected_cases_json['case2']['subscriptions']['add3'] = \
            {'events': [],
             'subscriptions': {}}
        self.assertDictEqual(response, expected_cases_json)
        self.__assert_subscriptions_synced('case2')

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

        self.put_with_status_check('/cases/junkcase/subscriptions',
                                   error='Case does not exist.',
                                   data=json.dumps(add1),
                                   headers=self.headers,
                                   content_type='application/json',
                                   status_code=OBJECT_DNE_ERROR)

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

        response = self.app.put('/cases/case1/subscriptions',
                                data=add1,
                                headers=self.headers,
                                content_type='application/json')
        self.assertEqual(response._status_code, 400)

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
            response = self.app.put('/cases/case1/subscriptions',
                                    data=json.dumps(bad_json),
                                    headers=self.headers,
                                    content_type='application/json')
            self.assertEqual(response._status_code, 400)

    # def test_edit_controller_subscription(self):
    #     input_events = ["Scheduler Start", "Scheduler Shutdown", "Scheduler Paused", "Scheduler Resumed", "Job Added",
    #                     "Job Removed", "Job Executed", "Job Error", "unknown event"]
    #     output = [EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED,
    #               EVENT_SCHEDULER_RESUMED, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_JOB_EXECUTED,
    #               EVENT_JOB_ERROR]
    #     self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
    #                  content_type='application/json')
    #     edit1 = {"ancestry": ["controller"],
    #              "events": input_events}
    #     response = self.app.post('/cases/case1/subscriptions',
    #                              data=json.dumps(edit1),
    #                              headers=self.headers,
    #                              content_type='application/json')
    #     self.assertEqual(response.status_code, SUCCESS)
    #     response = json.loads(response.get_data(as_text=True))
    #     subs = {'controller': {'events': output, 'subscriptions': {}}}
    #     expected_cases_json = {'case1': CaseSubscriptions().as_json()}
    #     expected_cases_json['case1']['subscriptions'] = subs
    #     self.assertDictEqual(response, expected_cases_json)

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
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type = 'application/json')
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

        response = self.app.post('/cases/case2/subscriptions',
                                 data=json.dumps(edit1),
                                 headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)
        self.__assert_subscriptions_synced('case2')

        expected_cases_json['case2']['subscriptions']['sub7']['subscriptions']['sub4']['events'] \
            = ['c', 'd', 'e']

        response = self.app.post('/cases/case2/subscriptions',
                                 data=json.dumps(edit2),
                                 headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)

        expected_cases_json['case2']['subscriptions']['sub8']['events'] = []

        response = self.app.post('/cases/case2/subscriptions',
                                 data=json.dumps(edit3),
                                 headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_cases_json)
        self.__assert_subscriptions_synced('case2')

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
        self.post_with_status_check('/cases/case2/subscriptions',
                                    error='Case or element does not exist.',
                                    data=json.dumps(edit1),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=OBJECT_DNE_ERROR)

    def test_edit_subscription_invalid_case(self):
        edit = {"ancestry": [], "events": []}
        self.post_with_status_check('/cases/case1/subscriptions',
                                    error='Case or element does not exist.',
                                    data=json.dumps(edit),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=OBJECT_DNE_ERROR)

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

        response = self.app.post('/cases/case2/subscriptions',
                                 headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response._status_code, 400)

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
            response = self.app.post('/cases/case2/subscriptions',
                                     headers=self.headers,
                                     data=json.dumps(edit),
                                     content_type='application/json')
            self.assertEqual(response._status_code, 400)

    # def test_remove_subscription(self):
    #     sub1 = Subscription()
    #     sub2 = Subscription()
    #     sub3 = Subscription()
    #
    #     sub4 = Subscription(subscriptions={'sub1': sub1, 'sub2': sub2})
    #     sub5 = Subscription(subscriptions={'sub3': sub3})
    #     sub6 = Subscription()
    #
    #     sub7 = Subscription(subscriptions={'sub4': sub4})
    #     sub8 = Subscription(subscriptions={'sub5': sub5})
    #     sub9 = Subscription(subscriptions={'sub6': sub6})
    #     sub10 = Subscription()
    #
    #     sub11 = Subscription(subscriptions={'sub7': sub7, 'sub8': sub8})
    #     sub12 = Subscription(subscriptions={'sub9': sub9})
    #     sub13 = Subscription(subscriptions={'sub10': sub10})
    #
    #     sub11_name = construct_workflow_name_key('playbook', 'sub11')
    #     sub12_name = construct_workflow_name_key('playbook', 'sub12')
    #     sub13_name = construct_workflow_name_key('playbook', 'sub13')
    #     sub14 = Subscription(subscriptions={sub11_name: sub11, sub12_name: sub12, sub13_name: sub13})
    #
    #     case1 = CaseSubscriptions(subscriptions={'sub14': sub14})
    #
    #     sub15 = Subscription()
    #     sub16 = Subscription()
    #     sub17 = Subscription()
    #
    #     sub18 = Subscription(subscriptions={'sub15': sub15, 'sub16': sub16})
    #     sub19 = Subscription(subscriptions={'sub17': sub17})
    #     sub20 = Subscription()
    #
    #     sub18_name = construct_workflow_name_key('playbook', 'sub18')
    #     sub19_name = construct_workflow_name_key('playbook', 'sub19')
    #     sub20_name = construct_workflow_name_key('playbook', 'sub20')
    #     sub21 = Subscription(subscriptions={sub18_name: sub18})
    #     sub22 = Subscription(subscriptions={sub19_name: sub19, sub20_name: sub20})
    #
    #     case2 = CaseSubscriptions(subscriptions={'sub21': sub21, 'sub22': sub22})
    #
    #     set_subscriptions({'case1': case1, 'case2': case2})
    #     self.app.put('/cases/case1', headers=self.headers)
    #     self.app.put('/cases/case2', headers=self.headers)
    #     tree1 = {'sub14': {sub11_name: {'sub7': {'sub4': {'sub1': {},
    #                                                       'sub2': {}}},
    #                                     'sub8': {'sub5': {'sub3': {}}}},
    #                        sub12_name: {'sub9': {'sub6': {}}},
    #                        sub13_name: {'sub10': {}}}}
    #
    #     tree2 = {'sub21': {sub18_name: {'sub15': {},
    #                                     'sub16': {}}},
    #              'sub22': {sub19_name: {'sub17': {}},
    #                        sub20_name: {}}}
    #
    #     # test that construct expected json is working
    #     self.assertDictEqual({'case1': construct_case_json(tree1), 'case2': construct_case_json(tree2)},
    #                          subscriptions_as_json())
    #
    #     def test_removal(case, ancestry, expected_tree_1, expected_tree_2):
    #         post_data = {"ancestry": ancestry}
    #         response = self.app.delete('/cases/{0}/subscriptions'.format(case),
    #                                    data=json.dumps(post_data),
    #                                    headers=self.headers,
    #                                    content_type='application/json')
    #         self.assertEqual(response.status_code, SUCCESS)
    #         response = json.loads(response.get_data(as_text=True))
    #         expected_response = {'case1': construct_case_json(expected_tree_1),
    #                              'case2': construct_case_json(expected_tree_2)}
    #         self.assertDictEqual(response, expected_response)
    #         self.__assert_subscriptions_synced(case)
    #
    #     tree1_after_rem10 = {'sub14': {sub11_name: {'sub7': {'sub4': {'sub1': {},
    #                                                                   'sub2': {}}},
    #                                                 'sub8': {'sub5': {'sub3': {}}}},
    #                                    sub12_name: {'sub9': {'sub6': {}}},
    #                                    sub13_name: {}}}
    #
    #     test_removal('case1', ["sub14", "playbook", "sub13", "sub10"], tree1_after_rem10, tree2)
    #
    #     tree2_after_rem20 = {'sub21': {sub18_name: {'sub15': {},
    #                                                 'sub16': {}}},
    #                          'sub22': {sub19_name: {'sub17': {}}}}
    #     test_removal('case2', ["sub22", 'playbook', "sub20"], tree1_after_rem10, tree2_after_rem20)
    #
    #     tree1_after_rem9 = {'sub14': {sub11_name: {'sub7': {'sub4': {'sub1': {},
    #                                                                  'sub2': {}}},
    #                                                'sub8': {'sub5': {'sub3': {}}}},
    #                                   sub12_name: {},
    #                                   sub13_name: {}}}
    #     test_removal('case1', ["sub14", "playbook", "sub12", "sub9"], tree1_after_rem9, tree2_after_rem20)
    #
    #     tree1_after_rem4 = {'sub14': {sub11_name: {'sub7': {},
    #                                                'sub8': {'sub5': {'sub3': {}}}},
    #                                   sub12_name: {},
    #                                   sub13_name: {}}}
    #     test_removal('case1', ['sub14', 'playbook', 'sub11', 'sub7', 'sub4'], tree1_after_rem4, tree2_after_rem20)
    #
    #     tree2_after_rem18 = {'sub21': {},
    #                          'sub22': {sub19_name: {'sub17': {}}}}
    #     test_removal('case2', ['sub21', 'playbook', 'sub18'], tree1_after_rem4, tree2_after_rem18)
    #
    #     tree1_after_rem11 = {'sub14': {sub12_name: {},
    #                                    sub13_name: {}}}
    #     test_removal('case1', ['sub14', 'playbook', 'sub11'], tree1_after_rem11, tree2_after_rem18)
    #
    #     tree1_after_rem14 = {}
    #     test_removal('case1', ['sub14'], tree1_after_rem14, tree2_after_rem18)
    #
    #     tree2_after_rem22 = {'sub21': {}}
    #     test_removal('case2', ['sub22'], tree1_after_rem14, tree2_after_rem22)
    #
    #     tree2_after_rem21 = {}
    #     test_removal('case2', ['sub21'], tree1_after_rem14, tree2_after_rem21)

    def test_remove_subscription_invalid_case(self):
        data = {"ancestry": ["sub1"]}
        set_subscriptions({'case1': CaseSubscriptions(), 'case2': CaseSubscriptions()})
        self.delete_with_status_check('/cases/junkcase/subscriptions',
                                      error='Case or element does not exist.',
                                      data=json.dumps(data),
                                      headers=self.headers,
                                      content_type='application/json',
                                      status_code=OBJECT_DNE_ERROR)

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

        def test_junk_path(case, path):
            data = {"ancestry": path}
            self.delete_with_status_check('/cases/{0}/subscriptions'.format(case),
                                          error='Case or element does not exist.',
                                          data=json.dumps(data),
                                          headers=self.headers,
                                          content_type='application/json',
                                          status_code=OBJECT_DNE_ERROR)

        test_junk_path('case2', ["sub21", "sub18", "sub15", "sub20"])
        test_junk_path('case2', ["sub1"])
        test_junk_path('case1', ['sub21'])
        test_junk_path('case2', ["sub22", "sub20", "sub17"])

    def test_remove_subscription_no_json(self):
        data = {"ancestry": ["sub1"]}
        set_subscriptions({'case1': CaseSubscriptions(), 'case2': CaseSubscriptions()})
        response = self.app.delete('/cases/junkcase/subscriptions',
                                   data=data,
                                   headers=self.headers,
                                   content_type='application/json')
        self.assertEqual(response._status_code, 400)

    def test_remove_subscription_invalid_json(self):
        data = {"ancestry_bad": ["sub1"]}
        set_subscriptions({'case1': CaseSubscriptions(), 'case2': CaseSubscriptions()})
        response = self.app.delete('/cases/junkcase/subscriptions',
                                   data=json.dumps(data),
                                   headers=self.headers,
                                   content_type='application/json')
        self.assertEqual(response._status_code, 400)

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

        data = {'note': 'Note1', 'id': smallest_id}
        response = self.app.post('/api/events', data=json.dumps(data), headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_event)

        expected_event['note'] = 'Note2'

        data = {'note': 'Note2', 'id': smallest_id}
        response = self.app.post('/api/events', data=json.dumps(data), headers=self.headers,
                                 content_type='application/json')
        self.assertEqual(response.status_code, SUCCESS)
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

        data = {"note": 'Note2', "id": invalid_id}
        self.post_with_status_check('/api/events',
                                    error='Event does not exist.',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=OBJECT_DNE_ERROR)
