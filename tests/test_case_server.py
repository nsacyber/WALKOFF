import json
import os

import walkoff.case.database as case_database
import walkoff.case.subscription as case_subs
from walkoff.server.returncodes import *
from walkoff.serverdb.casesubscription import CaseSubscription
from walkoff.extensions import db
from tests.util.assertwrappers import orderless_list_compare
from tests.util.servertestcase import ServerTestCase
from tests.config import test_apps_path
from uuid import uuid4


class TestCaseServer(ServerTestCase):
    def setUp(self):
        case_database.initialize()
        self.cases1 = {'case1': {'id1': ['e1', 'e2', 'e3'],
                                 'id2': ['e1']},
                       'case2': {'id1': ['e2', 'e3']}}
        self.cases_overlap = {'case2': {'id3': ['e', 'b', 'c'],
                                        'id4': ['d']},
                              'case3': {'id1': ['a', 'b']}}
        self.cases2 = {'case3': {'id3': ['e', 'b', 'c'],
                                 'id4': ['d']},
                       'case4': {'id1': ['a', 'b']}}
        self.cases_all = dict(self.cases1)
        self.cases_all.update(self.cases2)

    def tearDown(self):
        for case in case_database.case_db.session.query(case_database.Case).all():
            case_database.case_db.session.delete(case)
        case_database.case_db.commit()
        for case in CaseSubscription.query.all():
            db.session.delete(case)
        db.session.commit()
        if os.path.exists(os.path.join(test_apps_path, 'case.json')):
            os.remove(os.path.join(test_apps_path, 'case.json'))

    def create_case(self, name):
        response = json.loads(
            self.app.post(
                'api/cases',
                headers=self.headers,
                data=json.dumps({'name': name}),
                content_type='application/json').get_data(as_text=True))
        case2_id = response['id']
        return case2_id

    def test_add_case(self):
        data = {'name': 'case1', 'note': 'Test'}
        response = self.post_with_status_check('/api/cases', headers=self.headers, data=json.dumps(data),
                                               content_type='application/json', status_code=OBJECT_CREATED)
        self.assertEqual(response, {'id': 1, 'name': 'case1', 'note': 'Test', 'subscriptions': []})
        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        case = cases_config[0]
        self.assertEqual(case.name, 'case1')
        self.assertEqual(case.subscriptions, [])

    def test_add_case_existing_cases(self):
        data = json.dumps({'name': 'case3'})
        self.app.post('api/cases', headers=self.headers, data=data, content_type='application/json')
        self.post_with_status_check(
            'api/cases',
            headers=self.headers,
            data=data,
            status_code=OBJECT_EXISTS_ERROR,
            content_type='application/json')

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case3']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case3'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, [])
        self.cases1.update({'case1': {}})

    def test_add_case_with_subscriptions(self):
        uid = str(uuid4())
        subscription = {'id': uid, 'events': ['a', 'b', 'c']}
        data = {'name': 'case1', 'note': 'Test', 'subscriptions': [subscription]}
        response = self.post_with_status_check(
            '/api/cases',
            headers=self.headers,
            data=json.dumps(data),
           content_type='application/json',
            status_code=OBJECT_CREATED)
        self.assertEqual(
            response,
            {'id': 1, 'name': 'case1', 'note': 'Test', 'subscriptions': [{'id': uid, 'events': ['a', 'b', 'c']}]})
        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case1'])
        #TODO: TEST MESSAGE SENT TO WORKERS

    def test_read_cases_typical(self):
        case1_id = self.create_case('case1')
        response = json.loads(
            self.app.post(
                'api/cases',
                headers=self.headers,
                data=json.dumps({'name': 'case2', "note": 'note1'}),
                content_type='application/json').get_data(as_text=True))
        case2_id = response['id']

        response = json.loads(
            self.app.post(
                'api/cases',
                headers=self.headers,
                data=json.dumps({'name': 'case3', "note": 'note2'}),
                content_type='application/json').get_data(as_text=True))
        case3_id = response['id']
        response = self.get_with_status_check('/api/cases', headers=self.headers)
        expected_response = [
            {'note': '', 'subscriptions': [], 'id': case1_id, 'name': 'case1'},
            {'note': 'note1', 'subscriptions': [], 'id': case2_id, 'name': 'case2'},
            {'note': 'note2', 'subscriptions': [], 'id': case3_id, 'name': 'case3'}]
        for case in response:
            self.assertIn(case, expected_response)

    def test_read_cases_none(self):
        response = self.get_with_status_check('/api/cases', headers=self.headers)
        self.assertListEqual(response, [])

    def test_read_case_not_found(self):
        self.get_with_status_check(
            '/api/cases/404',
            error='Case does not exist.',
            headers=self.headers,
            status_code=OBJECT_DNE_ERROR)

    def test_delete_case_only_case(self):
        case_id = self.create_case('case1')
        self.delete_with_status_check('api/cases/{0}'.format(case_id), headers=self.headers, status_code=NO_CONTENT)

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = []
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertListEqual(cases_config, [])

    def test_delete_case(self):
        case1_id = self.create_case('case1')
        self.app.post(
            'api/cases',
            headers=self.headers,
            data=json.dumps({'name': 'case2'}),
            content_type='application/json')
        self.delete_with_status_check('api/cases/{0}'.format(case1_id), headers=self.headers, status_code=NO_CONTENT)

        cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case2']
        orderless_list_compare(self, cases, expected_cases)

        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)

        self.assertEqual(cases_config[0].name, 'case2')
        self.assertEqual(cases_config[0].subscriptions, [])

    def test_delete_case_invalid_case(self):
        self.create_case('case1')
        self.create_case('case2')
        self.delete_with_status_check(
            'api/cases/3',
            error='Case does not exist.',
            headers=self.headers,
            status_code=OBJECT_DNE_ERROR)

        db_cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = list(self.cases1.keys())
        orderless_list_compare(self, db_cases, expected_cases)

        cases_config = CaseSubscription.query.all()
        orderless_list_compare(self, [case.name for case in cases_config], ['case1', 'case2'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, [])

    def test_delete_case_no_cases(self):
        self.delete_with_status_check(
            'api/cases/404',
            error='Case does not exist.',
            headers=self.headers,
            status_code=OBJECT_DNE_ERROR)

        db_cases = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = []
        orderless_list_compare(self, db_cases, expected_cases)

        cases_config = CaseSubscription.query.all()
        self.assertListEqual(cases_config, [])

    def put_patch_test(self, verb):
        uid = str(uuid4())
        send_func = self.put_with_status_check if verb == 'put' else self.patch_with_status_check
        response = json.loads(
            self.app.post(
                'api/cases',
                headers=self.headers,
                data=json.dumps({'name': 'case1'}),
                content_type='application/json').get_data(as_text=True))
        case1_id = response['id']
        self.app.post(
            'api/cases',
            headers=self.headers,
            data=json.dumps({'name': 'case2'}),
            content_type='application/json')
        data = {"name": "renamed",
                "note": "note1",
                "id": case1_id,
                "subscriptions": [{"id": uid, "events": ['a', 'b', 'c']}]}
        response = send_func(
            'api/cases',
            data=json.dumps(data),
            headers=self.headers,
            content_type='application/json',
            status_code=SUCCESS)

        self.assertDictEqual(
            response,
            {'note': 'note1',
             'subscriptions': [{'id': uid, 'events': ['a', 'b', 'c']}],
             'id': 1,
             'name': 'renamed'})

        result_cases = case_database.case_db.cases_as_json()
        case1_new_json = next((case for case in result_cases if case['name'] == "renamed"), None)
        self.assertIsNotNone(case1_new_json)
        self.assertDictEqual(case1_new_json, {'id': 1, 'name': 'renamed'})

    def test_edit_case_put(self):
        self.put_patch_test('put')

    def test_edit_case_patch(self):
        self.put_patch_test('patch')

    def test_edit_case_no_name(self):
        case2_id = self.create_case('case1')
        self.app.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                     content_type='application/json')
        data = {"note": "note1", "id": case2_id}
        response = self.put_with_status_check(
            'api/cases',
            data=json.dumps(data),
            headers=self.headers,
            content_type='application/json',
            status_code=SUCCESS)
        self.assertDictEqual(response, {'note': 'note1', 'subscriptions': [], 'id': 1, 'name': 'case1'})

    def test_edit_case_no_note(self):
        case1_id = self.create_case('case1')
        self.app.put(
            'api/cases',
            headers=self.headers,
            data=json.dumps({'name': 'case2'}),
            content_type='application/json')
        data = {"name": "renamed", "id": case1_id}
        response = self.put_with_status_check(
            'api/cases',
            data=json.dumps(data),
            headers=self.headers,
            content_type='application/json',
            status_code=SUCCESS)
        self.assertDictEqual(response, {'note': '', 'subscriptions': [], 'id': 1, 'name': 'renamed'})

    def test_edit_case_invalid_case(self):
        self.create_case('case1')
        self.create_case('case2')
        data = {"name": "renamed", "id": 404}
        self.put_with_status_check(
            'api/cases',
            data=json.dumps(data),
            headers=self.headers,
            content_type='application/json',
            status_code=OBJECT_DNE_ERROR)

    def test_export_cases(self):
        subscription = {'id': 'id1', 'events': ['a', 'b', 'c']}
        data = {'name': 'case1', 'note': 'Test', 'subscriptions': [subscription]}
        case = self.post_with_status_check(
            '/api/cases',
            headers=self.headers,
            data=json.dumps(data),
            content_type='application/json',
            status_code=OBJECT_CREATED)
        case = self.get_with_status_check('api/cases/{}?mode=export'.format(case['id']), headers=self.headers)
        case.pop('id', None)
        self.assertIn('name', case)
        self.assertListEqual(case['events'], [])

    def test_import_cases(self):
        subscription = {'id': 'id1', 'events': ['a', 'b', 'c']}
        data = {'name': 'case1', 'note': 'Test', 'subscriptions': [subscription]}

        path = os.path.join(test_apps_path, 'case.json')
        with open(path, 'w') as f:
            f.write(json.dumps(data, indent=4, sort_keys=True))

        files = {'file': (path, open(path, 'r'), 'application/json')}
        case = self.post_with_status_check(
            '/api/cases',
            headers=self.headers,
            status_code=OBJECT_CREATED,
            data=files,
            content_type='multipart/form-data')
        case.pop('id', None)
        self.assertDictEqual(case, data)

    def test_display_possible_subscriptions(self):
        response = self.get_with_status_check('/api/availablesubscriptions', headers=self.headers)
        from walkoff.events import EventType, WalkoffEvent
        self.assertSetEqual({event['type'] for event in response},
                            {event.name for event in EventType if event != EventType.other})
        for event_type in (event.name for event in EventType if event != EventType.other):
            events = next((event['events'] for event in response if event['type'] == event_type))
            self.assertSetEqual(set(events),
                                {event.signal_name for event in WalkoffEvent if
                                 event.event_type.name == event_type and event != WalkoffEvent.SendMessage})

