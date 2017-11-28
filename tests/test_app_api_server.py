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
        expected_apps = ['HelloWorldBounded', 'DailyQuote', 'HelloWorld']
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

    def test_extract_schema_with_object(self):
        test_json = {'name': 'a', 'description': 'something', 'type': 'object',
                     'schema': {'required': ['a', 'b'],
                                'properties': {'a': {'type': 'string'},
                                               'b': {'type': 'number'}}}}
        expected = {'name': 'a', 'description': 'something',
                    'schema': {'type': 'object',
                               'required': ['a', 'b'],
                               'properties': {'a': {'type': 'string'},
                                              'b': {'type': 'number'}}}}
        self.assertDictEqual(extract_schema(test_json), expected)

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
        action_api = core.config.config.app_apis['HelloWorldBounded']['actions']['pause']
        expected = {
            'returns': [{'status': 'Success', 'description': 'successfully paused', 'schema': {'type': 'number'}},
                        {'status': 'UnhandledException', 'description': 'Exception occurred in action'},
                        {'status': 'InvalidInput', 'description': 'Input into the action was invalid'}],
            'run': 'main.Main.pause',
            'description': 'Pauses execution',
            'parameters': [
                {'schema': {'type': 'number'}, 'name': 'seconds', 'description': 'Seconds to pause', 'required': True}]}
        formatted = format_app_action_api(action_api, "HelloWorldBounded", "actions")
        self.assertSetEqual(set(formatted.keys()), set(expected.keys()))
        self.assertEqual(formatted['run'], expected['run'])
        self.assertEqual(formatted['description'], expected['description'])
        self.assertEqual(len(formatted['returns']), len(expected['returns']))
        for return_ in formatted['returns']:
            self.assertIn(return_, expected['returns'])
        self.assertEqual(len(formatted['parameters']), len(expected['parameters']))
        for parameter in formatted['parameters']:
            self.assertIn(parameter, expected['parameters'])

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
                        {'name': 'username', 'placeholder': 'user', 'required': True, 'schema': {'type': 'string'}},
                        {'name': 'password', 'placeholder': 'pass', 'encrypted': True, 'required': True,
                         'schema': {'type': 'string', 'minimumLength': 6}}]}
        self.assertSetEqual(set(formatted.keys()), set(expected.keys()))
        self.assertEqual(formatted['name'], expected['name'])
        self.assertEqual(formatted['description'], expected['description'])
        for field in formatted['fields']:
            self.assertIn(field, expected['fields'])

    def test_read_all_app_apis(self):
        response = self.app.get('/api/apps/apis', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, [app['name'] for app in response],
                               ['HelloWorldBounded', 'DailyQuote', 'HelloWorld'])

    def test_read_all_app_apis_with_field(self):
        response = self.app.get('/api/apps/apis?field_name=action_apis', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, [app['name'] for app in response],
                               ['HelloWorldBounded', 'DailyQuote', 'HelloWorld'])
        for app in response:
            self.assertSetEqual(set(app.keys()), {'name', 'action_apis'})

    def test_read_all_app_apis_with_device(self):
        response = self.app.get('/api/apps/apis?field_name=device_apis', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, [app['name'] for app in response],
                               ['HelloWorldBounded', 'DailyQuote', 'HelloWorld'])
        for app in response:
            self.assertSetEqual(set(app.keys()), {'name', 'device_apis'})

    def test_read_all_app_apis_with_field_field_dne(self):
        response = self.app.get('/api/apps/apis?field_name=invalid', headers=self.headers)
        self.assertEqual(response.status_code, BAD_REQUEST)

    def test_read_app_api(self):
        response = self.app.get('/api/apps/apis/HelloWorldBounded', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertSetEqual(set(response.keys()), {'name', 'tags', 'info', 'external_docs',
                                                   'action_apis', 'device_apis',
                                                   'condition_apis', 'transform_apis'})
        self.assertEqual(response['name'], 'HelloWorldBounded')

    def test_read_app_api_app_dne(self):
        response = self.app.get('/api/apps/apis/Invalid', headers=self.headers)
        self.assertEqual(response.status_code, OBJECT_DNE_ERROR)

    def test_read_app_api_field(self):
        response = self.app.get('/api/apps/apis/HelloWorldBounded/info', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertSetEqual(set(response.keys()), {'version', 'title', 'contact', 'license', 'description'})

    def test_read_app_api_field_app_dne(self):
        response = self.app.get('/api/apps/apis/Invalid/info', headers=self.headers)
        self.assertEqual(response.status_code, OBJECT_DNE_ERROR)

    def test_read_app_api_field_field_dne(self):
        response = self.app.get('/api/apps/apis/HelloWorldBounded/invalid', headers=self.headers)
        self.assertEqual(response.status_code, BAD_REQUEST)
