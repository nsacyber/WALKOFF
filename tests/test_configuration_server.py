import json

from flask import current_app

import walkoff.config.config
from tests.util.servertestcase import ServerTestCase
from walkoff.server.returncodes import *


class TestConfigurationServer(ServerTestCase):
    def setUp(self):
        config_fields = [x for x in dir(walkoff.config.config) if
                         not x.startswith('__') and type(getattr(walkoff.config.config, x)).__name__
                         in ['str', 'unicode']]
        self.original_configs = {key: getattr(walkoff.config.config, key) for key in config_fields}
        try:
            with open(walkoff.config.config.Config.CONFIG_PATH) as config_file:
                self.original_config_file = config_file.read()
        except:
            self.original_config_file = '{}'

    def tearDown(self):
        for key, value in self.original_configs.items():
            setattr(walkoff.config.config.Config, key, value)
        with open(walkoff.config.config.Config.CONFIG_PATH, 'w') as config_file:
            config_file.write(self.original_config_file)

    def test_get_configuration(self):
        expected = {'workflows_path': walkoff.config.config.Config.WORKFLOWS_PATH,
                    'db_path': walkoff.config.config.Config.DB_PATH,
                    'case_db_path': walkoff.config.config.Config.CASE_DB_PATH,
                    'log_config_path': walkoff.config.config.Config.LOGGING_CONFIG_PATH,
                    'host': walkoff.config.config.Config.HOST,
                    'port': int(walkoff.config.config.Config.PORT),
                    'walkoff_db_type': walkoff.config.config.Config.WALKOFF_DB_TYPE,
                    'case_db_type': walkoff.config.config.Config.CASE_DB_TYPE,
                    'clear_case_db_on_startup': bool(walkoff.config.config.Config.REINITIALIZE_CASE_DB_ON_STARTUP),
                    'number_threads_per_process': int(walkoff.config.config.Config.NUM_THREADS_PER_PROCESS),
                    'number_processes': int(walkoff.config.config.Config.NUMBER_PROCESSES),
                    'access_token_duration': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds / 60),
                    'refresh_token_duration': int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days),
                    'zmq_results_address': walkoff.config.config.Config.ZMQ_RESULTS_ADDRESS,
                    'zmq_communication_address': walkoff.config.config.Config.ZMQ_COMMUNICATION_ADDRESS,
                    'cache': None}
        response = self.get_with_status_check('/api/configuration', headers=self.headers)
        self.assertDictEqual(response, expected)

    def put_post_to_config(self, verb):
        send_func = self.put_with_status_check if verb == 'put' else self.patch_with_status_check
        data = {"db_path": 'db_path_reset',
                "host": 'host_reset',
                "port": 1100,
                "access_token_duration": 20,
                "refresh_token_duration": 35}
        send_func('/api/configuration', headers=self.headers, data=json.dumps(data), content_type='application/json')

        expected = {walkoff.config.config.Config.DB_PATH: 'db_path_reset',
                    walkoff.config.config.Config.HOST: 'host_reset',
                    walkoff.config.config.Config.PORT: 1100}

        for actual, expected_ in expected.items():
            self.assertEqual(actual, expected_)

        self.assertEqual(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds, 20 * 60)
        self.assertEqual(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days, 35)

    def test_set_configuration_put(self):
        self.put_post_to_config('put')

    def test_set_configuration_patch(self):
        self.put_post_to_config('patch')

    def test_set_configuration_invalid_token_durations(self):
        access_token_duration = current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds
        refresh_token_duration = current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days
        data = {"access_token_duration": 60 * 25,
                "refresh_token_duration": 1}
        self.put_with_status_check('/api/configuration', headers=self.headers, data=json.dumps(data),
                                   content_type='application/json', status_code=BAD_REQUEST)

        self.assertEqual(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].seconds, access_token_duration)
        self.assertEqual(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].days, refresh_token_duration)
