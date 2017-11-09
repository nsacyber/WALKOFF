import json

from flask import current_app

import core.config.config
import core.config.paths
from server.returncodes import *
from tests.util.assertwrappers import orderless_list_compare
from tests.util.servertestcase import ServerTestCase


class TestServer(ServerTestCase):

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
