import json
import copy
import os
from server import flaskserver as server
from tests.util.assertwrappers import orderless_list_compare
from tests.config import test_workflows_path_with_generated, test_workflows_path
import core.config.paths
import core.config.config
from tests.util.servertestcase import ServerTestCase


class TestServer(ServerTestCase):
    def setUp(self):
        config_fields = [x for x in dir(core.config.config) if
                         not x.startswith('__') and type(getattr(core.config.config, x)).__name__
                         in ['str', 'unicode']]
        path_fields = [x for x in dir(core.config.paths) if (not x.startswith('__')
                                                             and type(getattr(core.config.paths, x)).__name__
                                                             in ['str', 'unicode'])]
        self.original_configs = {key: getattr(core.config.config, key) for key in config_fields}
        self.original_paths = {key: getattr(core.config.paths, key) for key in path_fields}

    def preTearDown(self):
        for key, value in self.original_paths.items():
            setattr(core.config.paths, key, value)

    def tearDown(self):
        for key, value in self.original_configs.items():
            setattr(core.config.config, key, value)

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
                         not x.startswith('__')
                         and type(getattr(core.config.config, x)).__name__ in ['str', 'unicode', 'int']]
        path_fields = [x for x in dir(core.config.paths) if
                       (not x.startswith('__')
                        and type(getattr(core.config.paths, x)).__name__ in ['str', 'unicode'])]
        config_fields = list(set(config_fields) - set(path_fields))
        configs = {key: getattr(core.config.config, key) for key in config_fields}
        paths = {key: getattr(core.config.paths, key) for key in path_fields}
        for key, value in paths.items():
            response = self.app.get('/configuration/{0}'.format(key), headers=self.headers)
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            self.assertEqual(response[key], value)

        for key, value in configs.items():
            response = self.app.get('/configuration/{0}'.format(key), headers=self.headers)
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            self.assertEqual(response[key], str(value))

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
                "apps_path": core.config.paths.apps_path,
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

        self.post_with_status_check('/configuration/set', 'success', headers=self.headers, data=data)

        config_fields = [x for x in dir(core.config.config) if (not x.startswith('__') and
                                                                type(getattr(core.config.config, x)).__name__
                                                                in ['str', 'unicode'])]
        path_fields = [x for x in dir(core.config.paths) if (not x.startswith('__') and
                                                             type(getattr(core.config.paths, x)).__name__
                                                             in ['str', 'unicode'])]
        orderless_list_compare(self, config_fields, original_config_fields)
        orderless_list_compare(self, path_fields, original_path_fields)

        for key in data.keys():
            self.assertIn(key, (set(config_fields) | set(path_fields)))

        config_fields = list(set(config_fields) - set(path_fields))
        configs = {key: getattr(core.config.config, key) for key in config_fields}
        paths = {key: getattr(core.config.paths, key) for key in path_fields}

        for key, value in configs.items():
            if key in data:
                self.assertEqual(value, data[key])

        for key, value in paths.items():
            if key in data:
                self.assertEqual(value, data[key])

    def test_set_apps_path(self):
        original_function_info = copy.deepcopy(core.config.config.function_info)
        modified_function_info = copy.deepcopy(core.config.config.function_info)
        modified_function_info['testApp'] = {}
        data = {"apps_path": core.config.paths.apps_path}
        self.post_with_status_check('/configuration/set', 'success', headers=self.headers, data=data)
        self.assertDictEqual(core.config.config.function_info, original_function_info)

    def test_set_workflows_path(self):
        workflow_files = [os.path.splitext(workflow)[0]
                          for workflow in os.listdir(core.config.paths.workflows_path)
                          if workflow.endswith('.workflow')]
        self.app.post('/playbook/test_playbook/add', headers=self.headers)
        original_workflow_keys = list(server.running_context.controller.workflows.keys())
        data = {"apps_path": core.config.paths.apps_path,
                "workflows_path": test_workflows_path}
        self.post_with_status_check('/configuration/set', 'success', headers=self.headers, data=data)
        self.assertNotEqual(len(server.running_context.controller.workflows.keys()), len(original_workflow_keys))
        new_files = [os.path.splitext(workflow)[0]
                     for workflow in os.listdir(test_workflows_path_with_generated) if workflow.endswith('.workflow')]
        self.assertNotEqual(len(new_files), len(workflow_files))
