import json
import copy
import os
from server import flaskserver as server
from tests.util.assertwrappers import orderless_list_compare
from tests.config import test_workflows_path_with_generated, test_workflows_path
import core.config.paths
import core.config.config
from tests.util.servertestcase import ServerTestCase
from server.return_codes import *


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
        self.assertEqual(response.status_code, SUCCESS)

    def test_list_apps(self):
        expected_apps = ['HelloWorld', 'DailyQuote']
        response = self.app.get('/apps', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        orderless_list_compare(self, response['apps'], expected_apps)

    def test_list_widgets(self):
        expected = {'HelloWorld': ['testWidget', 'testWidget2'], 'DailyQuote': []}
        response = self.app.get('/widgets', headers=self.headers)
        self.assertEqual(response.status_code, SUCCESS)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected)

    def test_read_filters(self):
        response = self.get_with_status_check('/filters', headers=self.headers)
        expected = {'sub_top_filter': {'args': []},
                    'mod1_filter2': {'args': [{'required': True, 'type': 'number', 'name': 'arg1'}]},
                    'mod1_filter1': {'args': []},
                    'sub1_filter1': {'args': []},
                    'length': {'args': [], 'description': 'Returns the length of a collection'},
                    'sub1_filter3': {'args': []},
                    'filter1': {'args': []}, 'Top Filter': {'args': []}}
        self.assertDictEqual(response, {'filters': expected})

    def test_read_flags(self):
        response = self.get_with_status_check('/flags', headers=self.headers)
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
            'mod2_flag2': {'args': []},
            'mod2_flag1': {'args': []},
            'sub1_top_flag': {'args': []}}
        self.assertDictEqual(response, {'flags': expected})

    def test_get_all_list_actions(self):
        expected_json = {
            'DailyQuote': ['quoteIntro', 'forismaticQuote', 'getQuote', 'repeatBackToMe'],
            'HelloWorld': ['pause', 'Add Three', 'repeatBackToMe', 'Buggy',
                           'returnPlusOne', 'helloWorld', 'Hello World', 'Add To Previous']}
        response = self.get_with_status_check('/apps/actions', headers=self.headers)
        orderless_list_compare(self, list(response.keys()), list(expected_json.keys()))
        for app, actions in expected_json.items():
            orderless_list_compare(self, response[app], actions)

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
            self.assertEqual(response.status_code, SUCCESS)
            response = json.loads(response.get_data(as_text=True))
            self.assertEqual(response[key], value)

        for key, value in configs.items():
            response = self.app.get('/configuration/{0}'.format(key), headers=self.headers)
            self.assertEqual(response.status_code, SUCCESS)
            response = json.loads(response.get_data(as_text=True))
            self.assertEqual(response[key], str(value))

        self.get_with_status_check('/configuration/junkName',
                                   error='Configuration key does not exist.',
                                   headers=self.headers,
                                   status_code=OBJECT_DNE_ERROR)

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

        self.post_with_status_check('/configuration/set', headers=self.headers, data=data)

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

    def test_set_workflows_path(self):
        workflow_files = [os.path.splitext(workflow)[0]
                          for workflow in os.listdir(core.config.paths.workflows_path)
                          if workflow.endswith('.workflow')]
        self.app.put('/playbooks/test_playbook', headers=self.headers)
        original_workflow_keys = list(server.running_context.controller.workflows.keys())
        data = {"apps_path": core.config.paths.apps_path,
                "workflows_path": test_workflows_path}
        self.post_with_status_check('/configuration/set', headers=self.headers, data=data)
        self.assertNotEqual(len(server.running_context.controller.workflows.keys()), len(original_workflow_keys))
        new_files = [os.path.splitext(workflow)[0]
                     for workflow in os.listdir(test_workflows_path_with_generated) if workflow.endswith('.workflow')]
        self.assertNotEqual(len(new_files), len(workflow_files))
