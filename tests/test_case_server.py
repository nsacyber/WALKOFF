import json
import os

import core.case.database as case_database
import core.case.subscription as case_subs
import core.config.paths
import tests.config
from core.case.subscription import set_subscriptions, clear_subscriptions, delete_cases
from server.returncodes import *
from server.database.casesubscription import CaseSubscription
from server.extensions import db
from tests.util.assertwrappers import orderless_list_compare
from tests.util.servertestcase import ServerTestCase


class TestCaseServer(ServerTestCase):
    def setUp(self):
        case_database.initialize()
        self.cases1 = {'case1': {'uid1': ['e1', 'e2', 'e3'],
                                 'uid2': ['e1']},
                       'case2': {'uid1': ['e2', 'e3']}}
        self.cases_overlap = {'case2': {'uid3': ['e', 'b', 'c'],
                                        'uid4': ['d']},
                              'case3': {'uid1': ['a', 'b']}}
        self.cases2 = {'case3': {'uid3': ['e', 'b', 'c'],
                                 'uid4': ['d']},
                       'case4': {'uid1': ['a', 'b']}}
        self.cases_all = dict(self.cases1)
        self.cases_all.update(self.cases2)

    def tearDown(self):
        case_database.case_db.tear_down()
        clear_subscriptions()
        for case in CaseSubscription.query.all():
            db.session.delete(case)
        db.session.commit()

    def __basic_case_setup(self):
        set_subscriptions(self.cases_all)

    def test_add_case_no_existing_cases(self):
        data = {'name': 'case1', 'note': 'Test'}
        response = self.put_with_status_check('/api/cases', headers=self.headers, data=json.dumps(data),
                                              content_type='application/json', status_code=OBJECT_CREATED)
        self.assertEqual(response, {'id': 1, 'name': 'case1', 'note': 'Test', 'subscriptions': []})
        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        case = cases_config[0]
        self.assertEqual(case.name, 'case1')
        self.assertEqual(case.subscriptions, '[]')
        self.assertDictEqual(case_subs.subscriptions, {'case1': {}})

    def test_add_case_existing_cases(self):
        set_subscriptions(self.cases1)
        response = self.put_with_status_check('api/cases', headers=self.headers, data=json.dumps({'name': 'case3'}),
                                              status_code=OBJECT_CREATED, content_type='application/json')
        self.assertEqual(response, {'id': 1, 'name': 'case3', 'note': '', 'subscriptions': []})
        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1', 'case2', 'case3']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case3'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, '[]')
        self.cases1.update({'case1': {}})
        self.assertDictEqual(case_subs.subscriptions, self.cases1)

    def test_add_case_duplicate_case_out_of_sync(self):
        set_subscriptions({'case1': {}})
        expected_json = {'id': 1, 'name': 'case1', 'note': '', 'subscriptions': []}
        response = self.put_with_status_check('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                                              status_code=OBJECT_CREATED, content_type='application/json')
        self.assertEqual(response, expected_json)

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case1'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, '[]')
        self.assertDictEqual(case_subs.subscriptions, {'case1': {}})

    def test_add_case_duplicate_case_in_sync(self):
        set_subscriptions({'case1': {}})
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        self.put_with_status_check('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                                   status_code=OBJECT_EXISTS_ERROR, content_type='application/json')

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case1'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, '[]')
        self.assertDictEqual(case_subs.subscriptions, {'case1': {}})

    def test_add_case_with_subscriptions(self):
        subscription = {'uid': 'uid1', 'events': ['a', 'b', 'c']}
        data = {'name': 'case1', 'note': 'Test', 'subscriptions': [subscription]}
        response = self.put_with_status_check('/api/cases', headers=self.headers, data=json.dumps(data),
                                              content_type='application/json', status_code=OBJECT_CREATED)
        self.assertEqual(response, {'id': 1, 'name': 'case1', 'note': 'Test',
                                    'subscriptions': [{'uid': 'uid1', 'events': ['a', 'b', 'c']}]})
        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case1'])
        self.assertDictEqual(case_subs.subscriptions, {'case1': {'uid1': ['a', 'b', 'c']}})

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
        expected_response = [{'note': '', 'subscriptions': [], 'id': case1_id, 'name': 'case1'},
                             {'note': 'note1', 'subscriptions': [], 'id': case2_id, 'name': 'case2'},
                             {'note': 'note2', 'subscriptions': [], 'id': case3_id, 'name': 'case3'}]
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
        cases_config = CaseSubscription.query.all()
        self.assertListEqual(cases_config, [])
        self.assertDictEqual(case_subs.subscriptions, {})

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

        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)

        self.assertEqual(cases_config[0].name, 'case2')
        self.assertEqual(cases_config[0].subscriptions, '[]')
        self.assertDictEqual(case_subs.subscriptions, {'case2': {}})

    def test_delete_case_invalid_case(self):
        set_subscriptions(self.cases1)
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type='application/json')
        self.delete_with_status_check('api/cases/3',
                                      error='Case does not exist.',
                                      headers=self.headers,
                                      status_code=OBJECT_DNE_ERROR)

        db_cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = list(self.cases1.keys())
        orderless_list_compare(self, db_cases, expected_cases)

        cases_config = CaseSubscription.query.all()
        orderless_list_compare(self, [case.name for case in cases_config], ['case1', 'case2'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, '[]')
        self.assertDictEqual(case_subs.subscriptions, self.cases1)

    def test_delete_case_no_cases(self):
        self.delete_with_status_check('api/cases/404',
                                      error='Case does not exist.',
                                      headers=self.headers,
                                      status_code=OBJECT_DNE_ERROR)

        db_cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = []
        orderless_list_compare(self, db_cases, expected_cases)

        cases_config = CaseSubscription.query.all()
        self.assertListEqual(cases_config, [])

    def test_edit_case(self):
        response = json.loads(self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                                           content_type='application/json').get_data(as_text=True))
        case1_id = response['id']
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type='application/json')
        data = {"name": "renamed",
                "note": "note1",
                "id": case1_id,
                "subscriptions": [{"uid": 'uid1', "events": ['a', 'b', 'c']}]}
        response = self.post_with_status_check('api/cases', data=json.dumps(data), headers=self.headers,
                                               content_type='application/json', status_code=SUCCESS)

        self.assertDictEqual(response, {'note': 'note1', 'subscriptions': [{"uid": 'uid1', "events": ['a', 'b', 'c']}],
                                        'id': 1, 'name': 'renamed'})

        result_cases = case_database.case_db.cases_as_json()
        case1_new_json = next((case for case in result_cases if case['name'] == "renamed"), None)
        self.assertIsNotNone(case1_new_json)
        self.assertDictEqual(case1_new_json, {'id': 1, 'name': 'renamed'})
        self.assertDictEqual(case_subs.subscriptions, {'renamed': {'uid1': ['a', 'b', 'c']}, 'case2': {}})

    def test_edit_case_no_name(self):
        response = json.loads(self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                                           content_type='application/json').get_data(as_text=True))
        case2_id = response['id']
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        data = {"note": "note1", "id": case2_id}
        response = self.post_with_status_check('api/cases', data=json.dumps(data), headers=self.headers,
                                               content_type='application/json', status_code=SUCCESS)
        self.assertDictEqual(response, {'note': 'note1', 'subscriptions': [], 'id': 1, 'name': 'case2'})

    def test_edit_case_no_note(self):
        response = json.loads(self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                                           content_type='application/json').get_data(as_text=True))
        case1_id = response['id']
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type='application/json')
        data = {"name": "renamed", "id": case1_id}
        response = self.post_with_status_check('api/cases', data=json.dumps(data), headers=self.headers,
                                               content_type='application/json', status_code=SUCCESS)
        self.assertDictEqual(response, {'note': '', 'subscriptions': [], 'id': 1, 'name': 'renamed'})

    def test_edit_case_invalid_case(self):
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case2'}),
                     content_type='application/json')
        data = {"name": "renamed", "id": 404}
        self.post_with_status_check('api/cases',
                                    error='Case does not exist.',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=OBJECT_DNE_ERROR)

    def test_export_cases_no_filename(self):
        self.__basic_case_setup()
        expected_subs = case_subs.subscriptions
        self.post_with_status_check('api/cases/export', headers=self.headers)
        self.assertIn('cases.json', os.listdir(tests.config.test_data_path))
        with open(core.config.paths.default_case_export_path, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            read_json = json.loads(read_file)
        self.assertDictEqual(read_json, expected_subs)

    def test_export_cases_with_filename(self):
        self.__basic_case_setup()
        expected_subs = case_subs.subscriptions
        filename = os.path.join(tests.config.test_data_path, 'case_other.json')
        data = {"filename": filename}
        self.post_with_status_check('api/cases/export', headers=self.headers, data=json.dumps(data),
                                    content_type='application/json')
        self.assertIn('case_other.json', os.listdir(tests.config.test_data_path))
        with open(filename, 'r') as appdevice_file:
            read_file = appdevice_file.read()
            read_file = read_file.replace('\n', '')
            read_json = json.loads(read_file)
        self.assertDictEqual(read_json, expected_subs)

    def __assert_subscriptions_synced(self, case_name):
        cases_config = CaseSubscription.query.filter_by(name=case_name).all()
        self.assertEqual(len(cases_config), 1)
        case = cases_config[0]
        self.assertIn(case_name, case_subs.subscriptions)
        stored_subs = {sub['uid']: sub['events'] for sub in json.loads(case.subscriptions)}
        self.assertDictEqual(stored_subs, case_subs.subscriptions[case_name])

    def test_import_cases_no_filename(self):
        self.__basic_case_setup()
        self.post_with_status_check('api/cases/export', headers=self.headers)
        # essentially add two more cases, swap contents of case 1 and 2 in case_subscriptions
        delete_cases(['case1' 'case2'])

        response = self.get_with_status_check('api/cases/import', headers=self.headers)
        expected_subs = {'case1': {'uid2': ['e1'],
                                   'uid1': ['e1', 'e2', 'e3']},
                         'case3': {'uid4': ['d'],
                                   'uid3': ['e', 'b', 'c']},
                         'case2': {'uid1': ['e2', 'e3']},
                         'case4': {'uid1': ['a', 'b']}}
        self.assertDictEqual(response, {'cases': expected_subs})
        self.assertDictEqual(case_subs.subscriptions, expected_subs)
        for case in ['case1', 'case2', 'case3', 'case4']:
            self.__assert_subscriptions_synced(case)

    def test_import_cases_with_filename(self):
        self.__basic_case_setup()
        filename = os.path.join(tests.config.test_data_path, 'case_other.json')
        data = {"filename": filename}
        self.post_with_status_check('api/cases/export', headers=self.headers, data=json.dumps(data),
                                    content_type='application/json')
        # essentially add two more cases, swap contents of case 1 and 2 in case_subscriptions
        delete_cases(['case1' 'case2'])
        response = self.get_with_status_check('api/cases/import', headers=self.headers, data=json.dumps(data),
                                              content_type='application/json')
        expected_subs = {'case1': {'uid2': ['e1'], 'uid1': ['e1', 'e2', 'e3']},
                         'case3': {'uid4': ['d'], 'uid3': ['e', 'b', 'c']},
                         'case2': {'uid1': ['e2', 'e3']},
                         'case4': {'uid1': ['a', 'b']}}
        self.assertDictEqual(response, {'cases': expected_subs})
        self.assertDictEqual(case_subs.subscriptions, expected_subs)
        for case in ['case1', 'case2', 'case3', 'case4']:
            self.__assert_subscriptions_synced(case)

    def test_display_possible_subscriptions(self):
        response = self.get_with_status_check('/api/availablesubscriptions', headers=self.headers)
        from core.events import EventType, WalkoffEvent
        self.assertSetEqual({event['type'] for event in response},
                            {event.name for event in EventType if event != EventType.other})
        for event_type in (event.name for event in EventType if event != EventType.other):
            events = next((event['events'] for event in response if event['type'] == event_type))
            self.assertSetEqual(set(events),
                                {event.signal_name for event in WalkoffEvent if event.event_type.name == event_type and event != WalkoffEvent.SendMessage})
