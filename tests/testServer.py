import unittest
import json

from server import flaskServer as server
from tests.util.assertwrappers import orderless_list_compare
from tests.config import test_apps_path
import core.config.paths
import core.config.config


class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)

        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)
        core.config.paths.apps_path = test_apps_path

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}
        config_fields = [x for x in dir(core.config.config) if
                         not x.startswith('__') and type(getattr(core.config.config, x)) == str]
        path_fields = [x for x in dir(core.config.paths) if (not x.startswith('__')
                                                             and type(getattr(core.config.paths, x)) == str)]
        self.original_configs = {key: getattr(core.config.config, key) for key in config_fields}
        self.original_paths = {key: getattr(core.config.paths, key) for key in path_fields}

    def tearDown(self):
        for key, value in self.original_configs.items():
            setattr(core.config.config, key, value)
        for key, value in self.original_paths.items():
            setattr(core.config.paths, key, value)



    def test_login(self):
        response = self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_list_apps(self):
        expected_apps = ['HelloWorld']
        response = self.app.get('/apps/', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, response['apps'], expected_apps)

    def test_get_all_list_actions(self):
        expected_json = {"HelloWorld": ['helloWorld', 'repeatBackToMe', 'returnPlusOne', 'pause']}
        response = self.app.get('/apps/actions', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, response.keys(), expected_json.keys())
        for app, functions in response.items():
            orderless_list_compare(self, functions, expected_json[app])

    def test_get_configuration(self):
        config_fields = [x for x in dir(core.config.config) if
                         not x.startswith('__') and type(getattr(core.config.config, x)) == str]
        path_fields = [x for x in dir(core.config.paths) if (not x.startswith('__')
                                                             and type(getattr(core.config.paths, x)) == str)]
        configs = {key: getattr(core.config.config, key) for key in config_fields}
        paths = {key: getattr(core.config.paths, key) for key in path_fields}

        for key, value in configs.items():
            response = self.app.get('/configuration/{0}'.format(key), headers=self.headers)
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            self.assertEqual(response[key], value)

        for key, value in paths.items():
            response = self.app.get('/configuration/{0}'.format(key), headers=self.headers)
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            self.assertEqual(response[key], value)

        response = self.app.get('/configuration/junkName', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response['junkName'], "Error: key not found")

    def test_set_configuration(self):
        original_config_fields = [x for x in dir(core.config.config) if (not x.startswith('__') and
                                                                         type(getattr(core.config.config, x)).__name__
                                                                         in ['str', 'unicode'])]
        original_path_fields = [x for x in dir(core.config.paths) if (not x.startswith('__') and
                                                                      type(getattr(core.config.paths, x)).__name__
                                                                      in ['str', 'unicode'])]
        data = {"templates_path": 'templates_path_reset',
                "workflows_path": 'workflows_path_reset',
                "profile_visualizations_path": 'profile_visualizations_path_reset',
                "keywords_path": 'keywords_path_reset',
                "db_path": 'db_path_reset',
                "tls_version": 'tls_version_reset',
                "https": 'true',
                "private_key_path": 'private_key_path',
                "debug": 'false',
                "default_server": 'default_server_reset',
                "host": 'host_reset',
                "port": 'port_reset'}

        response = self.app.post('/configuration/set', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response['status'], "success")

        config_fields = [x for x in dir(core.config.config) if (not x.startswith('__') and
                                                                type(getattr(core.config.config, x)).__name__
                                                                in ['str', 'unicode'])]
        path_fields = [x for x in dir(core.config.paths) if (not x.startswith('__') and
                                                             type(getattr(core.config.paths, x)).__name__
                                                             in ['str', 'unicode'])]
        orderless_list_compare(self, config_fields, original_config_fields)
        orderless_list_compare(self, path_fields, original_path_fields)

        for key in data.keys():
            self.assertIn(key, config_fields)

        config_fields = list(set(config_fields) - set(path_fields))
        configs = {key: getattr(core.config.config, key) for key in config_fields}
        paths = {key: getattr(core.config.paths, key) for key in path_fields}

        for key, value in configs.items():
            if key in data:
                self.assertEqual(value, data[key])

        for key, value in paths.items():
            if key in data:
                self.assertEqual(value, data[key])
