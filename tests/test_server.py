import json
from tests.util.assertwrappers import orderless_list_compare
import core.config.paths
import core.config.config
from tests.util.servertestcase import ServerTestCase
from server.returncodes import *
from flask import current_app


class TestServer(ServerTestCase):

    def test_list_apps(self):
        expected_apps = ['HelloWorld', 'DailyQuote']
        response = self.app.get('/api/apps', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, response, expected_apps)

    def test_list_apps_with_interfaces(self):
        expected_apps = ['HelloWorld']
        response = self.app.get('/api/apps?interfaces_only=true', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, response, expected_apps)

    def test_list_apps_with_device_types(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        core.config.config.app_apis.update({'TestApp': {'devices': {'test_type': {'fields': fields_json}}}})
        response = self.app.get('/api/apps?has_device_types=true', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('TestApp', response)
        # orderless_list_compare(self, response, ['TestApp'])

    def test_list_widgets(self):
        expected = {'HelloWorld': ['testWidget', 'testWidget2'], 'DailyQuote': []}
        response = self.app.get('/widgets', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(2, len(response))
        self.assertIn('HelloWorld', response)
        self.assertIn('DailyQuote', response)
        self.assertEqual(0, len(response['DailyQuote']))
        orderless_list_compare(self, expected['HelloWorld'], response['HelloWorld'])

    def test_read_filters(self):
        response = self.get_with_status_check('/api/filters', headers=self.headers)
        expected = {'sub_top_filter': {'args': []},
                    'mod1_filter2': {'args': [{'required': True, 'type': 'number', 'name': 'arg1'}]},
                    'mod1_filter1': {'args': []},
                    'sub1_filter1': {'args': [{'required': True, 'name': 'arg1',
                                               'schema': {
                                                   'type': 'object',
                                                   'properties': {'a': {'type': 'number'}, 'b': {'type': 'string'}}}}]},
                    'length': {'args': [], 'description': 'Returns the length of a collection'},
                    'sub1_filter3': {'args': []},
                    'filter1': {'args': []},
                    'Top Filter': {'args': []},
                    'complex': {'args': [{'required': True, 'name': 'arg',
                                          'schema': {
                                              'type': 'object',
                                              'properties': {'a': {'type': 'number'},
                                                             'c': {'items': {'type': 'integer'}, 'type': 'array'},
                                                             'b': {'type': 'number'}}}}]},
                    'select json': {'args': [{'required': True, 'type': 'string', 'name': 'element'}]}}
        self.assertDictEqual(response, {'filters': expected})

    def test_read_flags(self):
        response = self.get_with_status_check('/api/flags', headers=self.headers)
        expected = {
            'count':
                {'description': 'Compares two numbers',
                 'args': [{'name': 'operator',
                           'enum': ['g', 'ge', 'l', 'le', 'e'],
                           'description': "The comparison operator ('g', 'ge', etc.)",
                           'default': 'e',
                           'required': True,
                           'type': 'string'},
                          {'name': 'threshold',
                           'required': True,
                           'type': 'number',
                           'description': 'The value with which to compare the input'}]},
            'Top Flag': {'args': []},
            'regMatch': {'description': 'Matches an input against a regular expression',
                         'args': [{'name': 'regex',
                                   'required': True,
                                   'type': 'string',
                                   'description': 'The regular expression to match'}]},
            'mod1_flag1': {'args': []},
            'mod1_flag2': {'args': [{'required': True, 'type': 'integer', 'name': 'arg1'}]},
            'mod2_flag2': {'args': [{'required': True, 'name': 'arg1',
                                     'schema': {'type': 'object',
                                                'properties': {'a': {'type': 'integer'}, 'b': {'type': 'integer'}}}}]},
            'mod2_flag1': {'args': []},
            'sub1_top_flag': {'args': []}}
        self.assertDictEqual(response, {'flags': expected})

        # def test_get_all_list_actions(self):
        #     expected_reduced_json = {
        #         'DailyQuote': ['quoteIntro', 'forismaticQuote', 'getQuote', 'repeatBackToMe'],
        #         'HelloWorld': ['pause', 'Add Three', 'repeatBackToMe', 'Buggy',
        #                        'returnPlusOne', 'helloWorld', 'Hello World', 'Add To Previous']}
        #     response = self.get_with_status_check('/apps/actions', headers=self.headers)
        #     orderless_list_compare(self, list(response.keys()), list(expected_reduced_json.keys()))

    def test_get_device_types(self):
        fields_json = [{'name': 'test_name', 'type': 'integer', 'encrypted': False},
                       {'name': 'test2', 'type': 'string', 'encrypted': False}]
        fields_json2 = [{'name': 'test3', 'type': 'integer', 'encrypted': True}]
        core.config.config.app_apis.update({'TestApp': {'devices': {'test_type': {'fields': fields_json,
                                                                                  'description': 'desc'},
                                                                    'test_type2': {'fields': fields_json2}}}})
        response = self.app.get('/api/devicetypes', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        # expected = [{'fields': [{'encrypted': True, 'type': 'integer', 'name': 'test3'}],
        #              'app': 'TestApp',
        #              'name': 'test_type2'},
        #             {'fields': [{'encrypted': False, 'type': 'integer', 'name': 'test_name'},
        #                         {'encrypted': False, 'type': 'string', 'name': 'test2'}],
        #              'app': 'TestApp',
        #              'description': 'desc',
        #              'name': 'test_type'}]
        for device_type in response:
            if device_type['name'] == 'test_type':
                self.assertSetEqual(set(device_type.keys()), {'fields', 'app', 'name', 'description'})
            elif device_type['name'] == 'test_type2':
                self.assertSetEqual(set(device_type.keys()), {'fields', 'app', 'name'})
            # TODO: Fix this test.
            # If there are device types added to apps, this will fail, even though the test should pass.
            # else:
            #     self.fail()


class TestConfiguration(ServerTestCase):

    def setUp(self):
        config_fields = [x for x in dir(core.config.config) if
                         not x.startswith('__') and type(getattr(core.config.config, x)).__name__
                         in ['str', 'unicode']]
        path_fields = [x for x in dir(core.config.paths) if (not x.startswith('__')
                                                             and type(getattr(core.config.paths, x)).__name__
                                                             in ['str', 'unicode'])]
        self.original_configs = {key: getattr(core.config.config, key) for key in config_fields}
        self.original_paths = {key: getattr(core.config.paths, key) for key in path_fields}
        try:
            with open(core.config.paths.config_path) as config_file:
                self.original_config_file = config_file.read()
        except:
            self.original_config_file = '{}'

    def preTearDown(self):
        for key, value in self.original_paths.items():
            setattr(core.config.paths, key, value)

    def tearDown(self):
        for key, value in self.original_configs.items():
            setattr(core.config.config, key, value)
        with open(core.config.paths.config_path, 'w') as config_file:
            config_file.write(self.original_config_file)

    def test_get_configuration(self):
        expected = {'workflows_path': core.config.paths.workflows_path,
                    'templates_path': core.config.paths.templates_path,
                    'db_path': core.config.paths.db_path,
                    'case_db_path': core.config.paths.case_db_path,
                    'log_config_path': core.config.paths.logging_config_path,
                    'host': core.config.config.host,
                    'port': int(core.config.config.port),
                    'walkoff_db_type': core.config.config.walkoff_db_type,
                    'case_db_type': core.config.config.case_db_type,
                    'https': bool(core.config.config.https),
                    'tls_version': core.config.config.tls_version,
                    'clear_case_db_on_startup': bool(core.config.config.reinitialize_case_db_on_startup),
                    'number_processes': int(core.config.config.num_processes),
                    'access_token_duration': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds / 60),
                    'refresh_token_duration': int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days)}
        response = self.get_with_status_check('/api/configuration', headers=self.headers)
        self.assertDictEqual(response, expected)

    def test_set_configuration(self):
        data = {"templates_path": 'templates_path_reset',
                "workflows_path": 'workflows_path_reset',
                "db_path": 'db_path_reset',
                "tls_version": '1.1',
                "https": True,
                "host": 'host_reset',
                "port": 1100,
                "access_token_duration": 20,
                "refresh_token_duration": 35}
        self.post_with_status_check('/api/configuration', headers=self.headers, data=json.dumps(data),
                                    content_type='application/json')

        expected = {core.config.paths.workflows_path: 'workflows_path_reset',
                    core.config.paths.templates_path: 'templates_path_reset',
                    core.config.paths.db_path: 'db_path_reset',
                    core.config.config.host: 'host_reset',
                    core.config.config.port: 1100,
                    core.config.config.https: True}

        for actual, expected_ in expected.items():
            self.assertEqual(actual, expected_)

        self.assertEqual(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds, 20*60)
        self.assertEqual(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days, 35)

    def test_set_configuration_invalid_token_durations(self):
        access_token_duration = current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds
        refresh_token_duration = current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days
        templates_path = core.config.paths.templates_path
        data = {"templates_path": 'templates_path_reset',
                "access_token_duration": 60*25,
                "refresh_token_duration": 1}
        self.post_with_status_check('/api/configuration', headers=self.headers, data=json.dumps(data),
                                    content_type='application/json', status_code=BAD_REQUEST)

        self.assertEqual(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds, access_token_duration)
        self.assertEqual(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days, refresh_token_duration)
        self.assertEqual(core.config.paths.templates_path, templates_path)
