import unittest
import shutil
import json
import os
import core.config.config
import core.config.paths
import tests.config
import server.flaskserver


class ServerTestCase(unittest.TestCase):
    test_workflows_path = tests.config.test_workflows_path_with_generated

    @classmethod
    def setUpClass(cls):
        if cls != ServerTestCase and cls.setUp != ServerTestCase.setUp:
            original_setup = cls.setUp

            def setup_override(self, *args, **kwargs):
                ServerTestCase.setUp(self)
                return original_setup(self, *args, **kwargs)
            cls.setUp = setup_override

        if cls != ServerTestCase and cls.tearDown != ServerTestCase.tearDown:
            original_teardown = cls.tearDown

            def teardown_override(self, *args, **kwargs):
                cls.preTearDown(self)
                ServerTestCase.tearDown(self)
                return original_teardown(self, *args, **kwargs)

            cls.tearDown = teardown_override

        if (tests.config.test_data_dir_name not in os.listdir(tests.config.test_path)
                or os.path.isfile(tests.config.test_data_path)):
            if os.path.isfile(tests.config.test_data_path):
                os.remove(tests.config.test_data_path)
            os.makedirs(tests.config.test_data_path)

    @classmethod
    def tearDownClass(cls):
        if tests.config.test_data_path in os.listdir(tests.config.test_path):
            if os.path.isfile(tests.config.test_data_path):
                os.remove(tests.config.test_data_path)
            else:
                shutil.rmtree(tests.config.test_data_path)

    def setUp(self):
        core.config.paths.workflows_path = tests.config.test_workflows_path_with_generated
        core.config.paths.apps_path = tests.config.test_apps_path
        core.config.paths.default_appdevice_export_path = tests.config.test_appdevice_backup
        core.config.paths.default_case_export_path = tests.config.test_cases_backup
        if os.path.exists(tests.config.test_workflows_backup_path):
            shutil.rmtree(tests.config.test_workflows_backup_path)

        shutil.copytree(core.config.paths.workflows_path, tests.config.test_workflows_backup_path)

        self.app = server.flaskserver.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)

        key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": key}

        server.flaskserver.running_context.controller.workflows = {}
        server.flaskserver.running_context.controller.load_all_workflows_from_directory()

    def tearDown(self):
        shutil.rmtree(core.config.paths.workflows_path)
        shutil.copytree(tests.config.test_workflows_backup_path, core.config.paths.workflows_path)
        shutil.rmtree(tests.config.test_workflows_backup_path)
        for data_file in os.listdir(tests.config.test_data_path):
            os.remove(os.path.join(tests.config.test_data_path, data_file))

    def preTearDown(self):
        """
        If overridden, this function is run before ServerTestCase.tearDown is run
        :return: None
        """
        pass

    def __assert_url_access(self, url, method, status, status_code=200, **kwargs):
        if method.lower() == 'get':
            response = self.app.get(url, **kwargs)
        elif method.lower() == 'post':
            response = self.app.post(url, **kwargs)
        elif method.lower() == 'put':
            response = self.app.put(url, **kwargs)
        elif method.lower() == 'delete':
            response = self.app.delete(url, **kwargs)
        else:
            raise ValueError('method must be either get or post')
        self.assertEqual(response.status_code, status_code)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn('status', response)
        self.assertEqual(response['status'], status)
        return response

    def get_with_status_check(self, url, status, status_code=200, **kwargs):
        return self.__assert_url_access(url, 'get', status, status_code, **kwargs)

    def post_with_status_check(self, url, status, status_code=200, **kwargs):
        return self.__assert_url_access(url, 'post', status, status_code, **kwargs)

    def put_with_status_check(self, url, status, status_code=200, **kwargs):
        return self.__assert_url_access(url, 'put', status, status_code, **kwargs)

    def delete_with_status_check(self, url, status, status_code=200, **kwargs):
        return self.__assert_url_access(url, 'delete', status, status_code, **kwargs)