import json

import apps
import core.config.config
import core.config.paths
import tests.config
from server.endpoints.appapi import *
from tests.util.assertwrappers import orderless_list_compare
from tests.util.servertestcase import ServerTestCase


class TestAppApiServerFuncs(ServerTestCase):
    def setUp(self):
        self.original_apps_path = core.config.paths.apps_path
        core.config.paths.apps_path = tests.config.test_apps_path
        apps.clear_cache()
        apps.cache_apps(tests.config.test_apps_path)

    def tearDown(self):
        core.config.paths.apps_path = self.original_apps_path
        core.config.config.app_apis.pop('TestApp', None)

    def test_read_all_apps(self):
        expected_apps = ['HelloWorld', 'DailyQuote']
        response = self.app.get('/api/apps', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, response, expected_apps)

    def test_extract_schema(self):
        test_json = {'name': 'a', 'example': 42, 'description': 'something', 'type': 'number', 'minimum': 1}
        expected = {'name': 'a', 'example': 42, 'description': 'something', 'schema': {'type': 'number', 'minimum': 1}}
        self.assertDictEqual(extract_schema(test_json), expected)

    def test_extract_schema_unformatted_fields_specified(self):
        test_json = {'name': 'a', 'example': 42, 'description': 'something', 'type': 'number', 'minimum': 1}
        expected = {'name': 'a', 'example': 42,
                    'schema': {'description': 'something', 'type': 'number', 'minimum': 1}}
        self.assertDictEqual(extract_schema(test_json, unformatted_fields=('name', 'example')), expected)

    def test_format_returns(self):
        returns = {'Success': {'description': 'something 1'}, 'Return2': {'schema': {'type': 'number', 'minimum': 10}}}
        expected = [{'status': 'Success', 'description': 'something 1'},
                    {'status': 'Return2', 'schema': {'type': 'number', 'minimum': 10}},
                    {'status': 'UnhandledException', 'description': 'Exception occurred in action'},
                    {'status': 'InvalidInput', 'description': 'Input into the action was invalid'}]
        formatted = format_returns(returns)
        self.assertEqual(len(formatted), len(expected))
        for return_ in formatted:
            self.assertIn(return_, expected)

    def test_format_returns_with_event(self):
        returns = {'Success': {'description': 'something 1'},
                   'Return2': {'schema': {'type': 'number', 'minimum': 10}}}
        expected = [{'status': 'Success', 'description': 'something 1'},
                    {'status': 'Return2', 'schema': {'type': 'number', 'minimum': 10}},
                    {'status': 'UnhandledException', 'description': 'Exception occurred in action'},
                    {'status': 'InvalidInput', 'description': 'Input into the action was invalid'},
                    {'status': 'EventTimedOut', 'description': 'Action timed out out waiting for event'}]
        formatted = format_returns(returns, with_event=True)
        self.assertEqual(len(formatted), len(expected))
        for return_ in formatted:
            self.assertIn(return_, expected)

    def test_format_app_action_api(self):
        action_api = core.config.config.app_apis['HelloWorld']['actions']['pause']
        expected = {
            'returns': [{'status': 'Success', 'description': 'successfully paused', 'schema': {'type': 'number'}},
                        {'status': 'UnhandledException', 'description': 'Exception occurred in action'},
                        {'status': 'InvalidInput', 'description': 'Input into the action was invalid'}],
            'run': 'main.Main.pause',
            'description': 'Pauses execution',
            'parameters': [
                {'schema': {'required': True, 'type': 'number'}, 'name': 'seconds', 'description': 'Seconds to pause'}]}
        formatted = format_app_action_api(action_api)
        self.assertSetEqual(set(formatted.keys()), set(expected.keys()))
        self.assertEqual(formatted['run'], expected['run'])
        self.assertEqual(formatted['description'], expected['description'])
        self.assertEqual(len(formatted['returns']), len(expected['returns']))
        for return_ in formatted['returns']:
            self.assertIn(return_, expected['returns'])
        self.assertEqual(len(formatted['parameters']), len(expected['parameters']))
        for parameter in formatted['parameters']:
            self.assertIn(parameter, expected['parameters'])

    def test_format_app_action_api_with_event(self):
        action_api = core.config.config.app_apis['HelloWorld']['actions']['Sample Event']
        expected = {'returns': [{'status': 'Success', 'description': 'summation', 'schema': {'type': 'number'}},
                                {'status': 'UnhandledException', 'description': 'Exception occurred in action'},
                                {'status': 'InvalidInput', 'description': 'Input into the action was invalid'},
                                {'status': 'EventTimedOut', 'description': 'Action timed out out waiting for event'}],
                    'run': 'main.Main.sample_event',
                    'event': 'Event1',
                    'parameters': [{'schema': {'required': True, 'type': 'number'}, 'name': 'arg1'}]}

        formatted = format_app_action_api(action_api)
        self.assertSetEqual(set(formatted.keys()), set(expected.keys()))
        self.assertEqual(formatted['run'], expected['run'])
        self.assertEqual(formatted['event'], expected['event'])
        self.assertEqual(len(formatted['returns']), len(expected['returns']))
        for return_ in formatted['returns']:
            self.assertIn(return_, expected['returns'])
        self.assertEqual(len(formatted['parameters']), len(expected['parameters']))
        for parameter in formatted['parameters']:
            self.assertIn(parameter, expected['parameters'])

    def test_format_all_app_actions_api(self):
        action_api = {'Sample Event': core.config.config.app_apis['HelloWorld']['actions']['Sample Event']}
        expected = [{'returns': [{'status': 'Success', 'description': 'summation', 'schema': {'type': 'number'}},
                                 {'status': 'UnhandledException', 'description': 'Exception occurred in action'},
                                 {'status': 'InvalidInput', 'description': 'Input into the action was invalid'},
                                 {'status': 'EventTimedOut', 'description': 'Action timed out out waiting for event'}],
                     'run': 'main.Main.sample_event',
                     'event': 'Event1',
                     'parameters': [{'schema': {'required': True, 'type': 'number'}, 'name': 'arg1'}],
                     'name': 'Sample Event'}]
        action_api.update({'pause': core.config.config.app_apis['HelloWorld']['actions']['pause']})
        expected.append({
            'returns': [{'status': 'Success', 'description': 'successfully paused', 'schema': {'type': 'number'}},
                        {'status': 'UnhandledException', 'description': 'Exception occurred in action'},
                        {'status': 'InvalidInput', 'description': 'Input into the action was invalid'}],
            'run': 'main.Main.pause',
            'description': 'Pauses execution',
            'parameters': [
                {'schema': {'required': True, 'type': 'number'}, 'name': 'seconds', 'description': 'Seconds to pause'}],
            'name': 'pause'})
        formatted = format_all_app_actions_api(action_api)
        self.assertEqual(len(formatted), len(expected))
        for action in formatted:
            self.assertIn(action['name'], ('Sample Event', 'pause'))

    def test_format_device_api(self):
        device_api = {'description': 'Something',
                      'fields': [
                          {'name': 'username', 'placeholder': 'user', 'type': 'string', 'required': True},
                          {'name': 'password', 'placeholder': 'pass', 'type': 'string', 'required': True, 'encrypted':
                           True, 'minimumLength': 6}]}
        formatted = format_device_api_full(device_api, 'TestDev')
        expected = {'description': 'Something',
                    'name': 'TestDev',
                    'fields': [
                          {'name': 'username', 'placeholder': 'user', 'schema': {'type': 'string', 'required': True}},
                          {'name': 'password', 'placeholder': 'pass', 'encrypted': True,
                           'schema': {'type': 'string', 'required': True,'minimumLength': 6}}]}
        self.assertSetEqual(set(formatted.keys()), set(expected.keys()))
        self.assertEqual(formatted['name'], expected['name'])
        self.assertEqual(formatted['description'], expected['description'])
        for field in formatted['fields']:
            self.assertIn(field, expected['fields'])

    def test_read_all_app_apis(self):
        response = self.app.get('/api/apps/apis', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, [app['name'] for app in response], ['HelloWorld', 'DailyQuote'])

    def test_read_all_app_apis_with_field(self):
        response = self.app.get('/api/apps/apis?field_name=action_apis', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, [app['name'] for app in response], ['HelloWorld', 'DailyQuote'])
        for app in response:
            self.assertSetEqual(set(app.keys()), {'name', 'action_apis'})

    def test_read_all_app_apis_with_device(self):
        response = self.app.get('/api/apps/apis?field_name=device_apis', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, [app['name'] for app in response], ['HelloWorld', 'DailyQuote'])
        for app in response:
            self.assertSetEqual(set(app.keys()), {'name', 'device_apis'})

    def test_read_all_app_apis_with_field_field_dne(self):
        response = self.app.get('/api/apps/apis?field_name=invalid', headers=self.headers)
        self.assertEqual(response.status_code, BAD_REQUEST)

    def test_read_app_api(self):
        response = self.app.get('/api/apps/apis/HelloWorld', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertSetEqual(set(response.keys()), {'name', 'tags', 'info', 'external_docs',
                                                   'action_apis', 'device_apis',
                                                   'condition_apis', 'transform_apis'})
        self.assertEqual(response['name'], 'HelloWorld')

    def test_read_app_api_app_dne(self):
        response = self.app.get('/api/apps/apis/Invalid', headers=self.headers)
        self.assertEqual(response.status_code, OBJECT_DNE_ERROR)

    def test_read_app_api_field(self):
        response = self.app.get('/api/apps/apis/HelloWorld/info', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertSetEqual(set(response.keys()), {'version', 'title', 'contact', 'license', 'description'})

    def test_read_app_api_field_app_dne(self):
        response = self.app.get('/api/apps/apis/Invalid/info', headers=self.headers)
        self.assertEqual(response.status_code, OBJECT_DNE_ERROR)

    def test_read_app_api_field_field_dne(self):
        response = self.app.get('/api/apps/apis/HelloWorld/invalid', headers=self.headers)
        self.assertEqual(response.status_code, BAD_REQUEST)


