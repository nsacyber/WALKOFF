import json
import os

import walkoff.case.database as case_database
from walkoff.case.subscription import Subscription
from walkoff.server.returncodes import *
from walkoff.serverdb.casesubscription import CaseSubscription
from walkoff.extensions import db
from walkoff.server.endpoints.cases import convert_subscriptions, split_subscriptions
from tests.util.assertwrappers import orderless_list_compare
from tests.util.servertestcase import ServerTestCase
from uuid import uuid4
from mock import create_autospec, patch, call
from walkoff.case.logger import CaseLogger
from flask import current_app
import walkoff.config


class TestCaseServer(ServerTestCase):
    def setUp(self):
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
        self.logger = create_autospec(CaseLogger)
        current_app.running_context.case_logger = self.logger

    def tearDown(self):
        for case in current_app.running_context.case_db.session.query(case_database.Case).all():
            current_app.running_context.case_db.session.delete(case)
        current_app.running_context.case_db.commit()
        for case in CaseSubscription.query.all():
            db.session.delete(case)
        db.session.commit()
        if os.path.exists(os.path.join(walkoff.config.Config.APPS_PATH, 'case.json')):
            os.remove(os.path.join(walkoff.config.Config.APPS_PATH, 'case.json'))

    def create_case(self, name):
        response = json.loads(
            self.test_client.post(
                'api/cases',
                headers=self.headers,
                data=json.dumps({'name': name}),
                content_type='application/json').get_data(as_text=True))
        case2_id = response['id']
        return case2_id

    def test_create_case(self):
        data = {'name': 'case1', 'note': 'Test'}
        response = self.post_with_status_check('/api/cases', headers=self.headers, data=json.dumps(data),
                                               content_type='application/json', status_code=OBJECT_CREATED)
        self.assertEqual(response, {'id': 1, 'name': 'case1', 'note': 'Test', 'subscriptions': []})
        cases = [case.name for case in current_app.running_context.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        case = cases_config[0]
        self.assertEqual(case.name, 'case1')
        self.assertEqual(case.subscriptions, [])

    def test_convert_subscriptions_empty_list(self):
        self.assertListEqual(convert_subscriptions([]), [])

    def test_convert_subscriptions(self):
        self.assertEqual(
            convert_subscriptions([{'id': 1, 'events': ['a', 'b']}, {'id': 2, 'events': ['b', 'c', 'd', 'e']}]),
            [Subscription(1, ['a', 'b']), Subscription(2, ['b', 'c', 'd', 'e'])]
        )

    def test_split_subscriptions_empty_list(self):
        self.assertTupleEqual(split_subscriptions([]), ([], None))

    def test_split_subscriptions_no_controller(self):
        self.assertTupleEqual(
            split_subscriptions([Subscription(1, ['a', 'b']), Subscription(2, ['b', 'c', 'd', 'e'])]),
            ([Subscription(1, ['a', 'b']), Subscription(2, ['b', 'c', 'd', 'e'])], None)
        )

    def test_split_subscriptions_with_controller(self):
        self.assertTupleEqual(
            split_subscriptions(
                [Subscription(1, ['a']), Subscription('controller', ['d']), Subscription(2, ['b', 'c'])]),
            ([Subscription(1, ['a']), Subscription(2, ['b', 'c'])], Subscription('controller', ['d']))
        )

    def test_create_case_existing_cases(self):
        data = json.dumps({'name': 'case3'})
        self.test_client.post('api/cases', headers=self.headers, data=data, content_type='application/json')
        self.post_with_status_check(
            'api/cases',
            headers=self.headers,
            data=data,
            status_code=OBJECT_EXISTS_ERROR,
            content_type='application/json')

        cases = [case.name for case in current_app.running_context.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case3']
        orderless_list_compare(self, cases, expected_cases)
        cases_config = CaseSubscription.query.all()
        self.assertEqual(len(cases_config), 1)
        orderless_list_compare(self, [case.name for case in cases_config], ['case3'])
        for case in cases_config:
            self.assertEqual(case.subscriptions, [])
        self.cases1.update({'case1': {}})

    # @patch.object(current_app.running_context.executor, 'create_case')
    def test_create_case_with_subscriptions_no_controller(self):
        with patch.object(current_app.running_context.executor, 'create_case') as mock_create:
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
            cases = [case.name for case in current_app.running_context.case_db.session.query(case_database.Case).all()]
            expected_cases = ['case1']
            orderless_list_compare(self, cases, expected_cases)
            cases_config = CaseSubscription.query.all()
            self.assertEqual(len(cases_config), 1)
            orderless_list_compare(self, [case.name for case in cases_config], ['case1'])
            mock_create.assert_called_once_with(1, [Subscription(uid, ['a', 'b', 'c'])])

    # @patch.object(current_app.running_context.executor, 'create_case')
    def test_create_case_with_subscriptions_with_controller(self):
        with patch.object(current_app.running_context.executor, 'create_case') as mock_create:
            uid = str(uuid4())

            subscriptions = [{'id': uid, 'events': ['a', 'b', 'c']}, {'id': 'controller', 'events': ['a']}]
            data = {'name': 'case1', 'note': 'Test', 'subscriptions': subscriptions}
            response = self.post_with_status_check(
                '/api/cases',
                headers=self.headers,
                data=json.dumps(data),
                content_type='application/json',
                status_code=OBJECT_CREATED)
            self.assertEqual(
                response,
                {'id': 1, 'name': 'case1', 'note': 'Test', 'subscriptions': subscriptions})
            cases = [case.name for case in current_app.running_context.case_db.session.query(case_database.Case).all()]
            expected_cases = ['case1']
            orderless_list_compare(self, cases, expected_cases)
            cases_config = CaseSubscription.query.all()
            self.assertEqual(len(cases_config), 1)
            orderless_list_compare(self, [case.name for case in cases_config], ['case1'])
            mock_create.assert_called_once_with(1, [Subscription(uid, ['a', 'b', 'c'])])
            self.logger.add_subscriptions.assert_called_once()

    def test_read_cases_typical(self):
        case1_id = self.create_case('case1')
        response = json.loads(
            self.test_client.post(
                'api/cases',
                headers=self.headers,
                data=json.dumps({'name': 'case2', "note": 'note1'}),
                content_type='application/json').get_data(as_text=True))
        case2_id = response['id']

        response = json.loads(
            self.test_client.post(
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

    # @patch.object(current_app.running_context.executor, 'delete_case')
    def test_delete_case_only_case(self):
        with patch.object(current_app.running_context.executor, 'delete_case') as mock_delete:
            case_id = self.create_case('case1')
            self.delete_with_status_check('api/cases/{0}'.format(case_id), headers=self.headers, status_code=NO_CONTENT)

            cases = [case.name for case in current_app.running_context.case_db.session.query(case_database.Case).all()]
            expected_cases = []
            orderless_list_compare(self, cases, expected_cases)
            cases_config = CaseSubscription.query.all()
            self.assertListEqual(cases_config, [])
            mock_delete.assert_called_once_with(case_id)

    # @patch.object(current_app.running_context.executor, 'delete_case')
    def test_delete_case(self):
        with patch.object(current_app.running_context.executor, 'delete_case') as mock_delete:
            case1_id = self.create_case('case1')
            self.test_client.post(
                'api/cases',
                headers=self.headers,
                data=json.dumps({'name': 'case2'}),
                content_type='application/json')
            self.delete_with_status_check('api/cases/{0}'.format(case1_id), headers=self.headers, status_code=NO_CONTENT)

            cases = [case.name for case in current_app.running_context.case_db.session.query(case_database.Case).all()]
            expected_cases = ['case2']
            orderless_list_compare(self, cases, expected_cases)

            cases_config = CaseSubscription.query.all()
            self.assertEqual(len(cases_config), 1)

            self.assertEqual(cases_config[0].name, 'case2')
            self.assertEqual(cases_config[0].subscriptions, [])
            mock_delete.assert_called_once_with(case1_id)

    # @patch.object(current_app.running_context.executor, 'delete_case')
    def test_delete_case_invalid_case(self):
        with patch.object(current_app.running_context.executor, 'delete_case') as mock_delete:
            self.create_case('case1')
            self.create_case('case2')
            self.delete_with_status_check(
                'api/cases/3',
                error='Case does not exist.',
                headers=self.headers,
                status_code=OBJECT_DNE_ERROR)

            db_cases = [case.name for case in current_app.running_context.case_db.session.query(case_database.Case).all()]
            expected_cases = list(self.cases1.keys())
            orderless_list_compare(self, db_cases, expected_cases)

            cases_config = CaseSubscription.query.all()
            orderless_list_compare(self, [case.name for case in cases_config], ['case1', 'case2'])
            for case in cases_config:
                self.assertEqual(case.subscriptions, [])
            mock_delete.assert_not_called()

    # @patch.object(current_app.running_context.executor, 'delete_case')
    def test_delete_case_no_cases(self):
        with patch.object(current_app.running_context.executor, 'delete_case') as mock_delete:
            self.delete_with_status_check(
                'api/cases/404',
                error='Case does not exist.',
                headers=self.headers,
                status_code=OBJECT_DNE_ERROR)

            db_cases = [case.name for case in current_app.running_context.case_db.session.query(case_database.Case).all()]
            expected_cases = []
            orderless_list_compare(self, db_cases, expected_cases)

            cases_config = CaseSubscription.query.all()
            self.assertListEqual(cases_config, [])
            mock_delete.assert_not_called()

    def put_patch_test(self, verb, mock_update):
        uid = str(uuid4())
        send_func = self.put_with_status_check if verb == 'put' else self.patch_with_status_check
        response = json.loads(
            self.test_client.post(
                'api/cases',
                headers=self.headers,
                data=json.dumps({'name': 'case1'}),
                content_type='application/json').get_data(as_text=True))
        case1_id = response['id']
        self.test_client.post(
            'api/cases',
            headers=self.headers,
            data=json.dumps({'name': 'case2'}),
            content_type='application/json')
        subscriptions = [{"id": uid, "events": ['a', 'b', 'c']}, {'id': 'controller', 'events': ['a']}]
        data = {"name": "renamed",
                "note": "note1",
                "id": case1_id,
                "subscriptions": subscriptions}
        response = send_func(
            'api/cases',
            data=json.dumps(data),
            headers=self.headers,
            content_type='application/json',
            status_code=SUCCESS)

        self.assertDictEqual(
            response,
            {'note': 'note1',
             'subscriptions': subscriptions,
             'id': 1,
             'name': 'renamed'})
        mock_update.assert_called_once()
        self.logger.update_subscriptions.assert_called_once()

        result_cases = current_app.running_context.case_db.cases_as_json()
        case1_new_json = next((case for case in result_cases if case['name'] == "renamed"), None)
        self.assertIsNotNone(case1_new_json)
        self.assertDictEqual(case1_new_json, {'id': 1, 'name': 'renamed'})

    def test_edit_case_put(self):
        with patch.object(current_app.running_context.executor, 'update_case') as mock_update:
            self.put_patch_test('put', mock_update)

    def test_edit_case_patch(self):
        with patch.object(current_app.running_context.executor, 'update_case') as mock_update:
            self.put_patch_test('patch', mock_update)

    def test_edit_case_no_name(self):
        with patch.object(current_app.running_context.executor, 'update_case') as mock_update:
            case2_id = self.create_case('case1')
            self.test_client.put('api/cases', headers=self.headers, data=json.dumps({'name': 'case1'}),
                         content_type='application/json')
            data = {"note": "note1", "id": case2_id}
            response = self.put_with_status_check(
                'api/cases',
                data=json.dumps(data),
                headers=self.headers,
                content_type='application/json',
                status_code=SUCCESS)
            self.assertDictEqual(response, {'note': 'note1', 'subscriptions': [], 'id': 1, 'name': 'case1'})
            mock_update.assert_not_called()

    def test_edit_case_no_note(self):
        with patch.object(current_app.running_context.executor, 'update_case') as mock_update:
            case1_id = self.create_case('case1')
            self.test_client.put(
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
            mock_update.assert_not_called()

    def test_edit_case_invalid_case(self):
        with patch.object(current_app.running_context.executor, 'update_case') as mock_update:
            self.create_case('case1')
            self.create_case('case2')
            data = {"name": "renamed", "id": 404}
            self.put_with_status_check(
                'api/cases',
                data=json.dumps(data),
                headers=self.headers,
                content_type='application/json',
                status_code=OBJECT_DNE_ERROR)
            mock_update.assert_not_called()

    def test_export_cases(self):
        with patch.object(current_app.running_context.executor, 'create_case') as mock_create:
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
        with patch.object(current_app.running_context.executor, 'create_case') as mock_create:
            subscription = {'id': 'id1', 'events': ['a', 'b', 'c']}
            data = {'name': 'case1', 'note': 'Test', 'subscriptions': [subscription]}

            path = os.path.join(walkoff.config.Config.APPS_PATH, 'case.json')
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
            subscriptions = [Subscription('id1', ['a', 'b', 'c'])]
            mock_create.assert_called_once_with(1, subscriptions)

    def test_display_possible_subscriptions(self):
        response = self.get_with_status_check('/api/availablesubscriptions', headers=self.headers)
        from walkoff.events import EventType, WalkoffEvent
        self.assertSetEqual({event['type'] for event in response},
                            {event.name for event in EventType if event != EventType.other})
        for event_type in (event.name for event in EventType if event != EventType.other):
            events = next((event['events'] for event in response if event['type'] == event_type))
            self.assertSetEqual(set(events),
                                {event.signal_name for event in WalkoffEvent if
                                 event.event_type.name == event_type and event.is_loggable()})

    def test_send_cases_to_workers(self):
        with patch.object(current_app.running_context.executor, 'update_case') as mock_update:
            from walkoff.case.database import Case
            from walkoff.serverdb.casesubscription import CaseSubscription
            from walkoff.extensions import db
            from walkoff.server.blueprints.root import send_all_cases_to_workers
            ids = [str(uuid4()) for _ in range(4)]
            case1_subs = [{'id': ids[0], 'events': ['e1', 'e2', 'e3']}, {'id': ids[1], 'events': ['e1']}]
            case2_subs = [{'id': ids[0], 'events': ['e2', 'e3']}]
            case3_subs = [{'id': ids[2], 'events': ['e', 'b', 'c']}, {'id': ids[3], 'events': ['d']}]
            case4_subs = [{'id': ids[0], 'events': ['a', 'b']}]
            expected = []
            for i, case_subs in enumerate((case1_subs, case2_subs, case3_subs, case4_subs)):
                name = 'case{}'.format(i)
                new_case_subs = CaseSubscription(name, subscriptions=case_subs)
                db.session.add(new_case_subs)
                case = Case(name=name)
                current_app.running_context.case_db.session.add(case)
                current_app.running_context.case_db.session.commit()
                call_subs = [Subscription(sub['id'], sub['events']) for sub in case_subs]
                expected.append(call(case.id, call_subs))
                current_app.running_context.case_db.session.commit()
            send_all_cases_to_workers()
            mock_update.assert_has_calls(expected)
