import os
import shutil
import stat
import unittest

import walkoff.appgateway
import walkoff.config.config
import walkoff.config.paths
from tests.util import device_db_help
import tests.config
from walkoff.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from tests.util.mock_objects import *
from tests.util.thread_control import *
from walkoff.server.endpoints.appapi import *
from walkoff.server.returncodes import NO_CONTENT

if not getattr(__builtins__, 'WindowsError', None):
    class WindowsError(OSError): pass


def modified_setup_worker_env():
    import tests.config
    import walkoff.config.config
    walkoff.appgateway.cache_apps(tests.config.test_apps_path)
    walkoff.config.config.load_app_apis(apps_path=tests.config.test_apps_path)


class ServerTestCase(unittest.TestCase):
    test_workflows_path = tests.config.test_workflows_path_with_generated
    patch = True

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

        device_db_help.setup_dbs()

        walkoff.appgateway.cache_apps(path=tests.config.test_apps_path)
        walkoff.config.config.app_apis = {}
        walkoff.config.config.load_app_apis(apps_path=tests.config.test_apps_path)
        walkoff.config.config.num_processes = 2

        from walkoff.server import flaskserver
        cls.context = flaskserver.app.test_request_context()
        cls.context.push()

        from walkoff.server.app import create_user
        create_user()
        if cls.patch:
            MultiprocessedExecutor.initialize_threading = mock_initialize_threading
            MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
            MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
            flaskserver.running_context.executor.initialize_threading()
        else:
            from walkoff.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
            pids = spawn_worker_processes(worker_environment_setup=modified_setup_worker_env)
            flaskserver.running_context.executor.initialize_threading(pids)

    @classmethod
    def tearDownClass(cls):
        import walkoff.server.flaskserver
        if tests.config.test_data_path in os.listdir(tests.config.test_path):
            if os.path.isfile(tests.config.test_data_path):
                os.remove(tests.config.test_data_path)
            else:
                shutil.rmtree(tests.config.test_data_path)

        walkoff.server.flaskserver.running_context.executor.shutdown_pool()

        import walkoff.coredb.devicedb
        device_db_help.cleanup_device_db()
        walkoff.coredb.devicedb.device_db.tear_down()

        import walkoff.case.database as case_database
        case_database.case_db.tear_down()
        walkoff.appgateway.clear_cache()

    def setUp(self):
        import walkoff.server.flaskserver
        walkoff.config.paths.workflows_path = tests.config.test_workflows_path_with_generated
        walkoff.config.paths.apps_path = tests.config.test_apps_path
        walkoff.config.paths.default_appdevice_export_path = tests.config.test_appdevice_backup
        walkoff.config.paths.default_case_export_path = tests.config.test_cases_backup
        if os.path.exists(tests.config.test_workflows_backup_path):
            shutil.rmtree(tests.config.test_workflows_backup_path)

        shutil.copytree(walkoff.config.paths.workflows_path, tests.config.test_workflows_backup_path)

        self.app = walkoff.server.flaskserver.app.test_client(self)
        self.app.testing = True

        self.context = walkoff.server.flaskserver.app.test_request_context()
        self.context.push()

        post = self.app.post('/api/auth', content_type="application/json",
                             data=json.dumps(dict(username='admin', password='admin')), follow_redirects=True)
        key = json.loads(post.get_data(as_text=True))
        self.headers = {'Authorization': 'Bearer {}'.format(key['access_token'])}
        self.http_verb_lookup = {'get': self.app.get,
                                 'post': self.app.post,
                                 'put': self.app.put,
                                 'delete': self.app.delete,
                                 'patch': self.app.patch}

    def tearDown(self):
        import walkoff.coredb.devicedb
        walkoff.coredb.devicedb.device_db.session.rollback()

        shutil.rmtree(walkoff.config.paths.workflows_path)
        shutil.copytree(tests.config.test_workflows_backup_path, walkoff.config.paths.workflows_path)
        shutil.rmtree(tests.config.test_workflows_backup_path)
        for data_file in os.listdir(tests.config.test_data_path):
            try:
                os.remove(os.path.join(tests.config.test_data_path, data_file))
            except WindowsError as we:  # Windows sometimes makes files read only when created
                os.chmod(os.path.join(tests.config.test_data_path, data_file), stat.S_IWRITE)
                os.remove(os.path.join(tests.config.test_data_path, data_file))

    def preTearDown(self):
        """
        If overridden, this function is run before ServerTestCase.tearDown is run
        :return: None
        """
        pass

    def __assert_url_access(self, url, method, status_code, error, **kwargs):
        try:
            response = self.http_verb_lookup[method.lower()](url, **kwargs)
        except KeyError as e:
            import traceback
            traceback.print_exc()
            print(e)
            raise ValueError('method must be either get, put, post, patch, or delete')
        self.assertEqual(response.status_code, status_code)
        if status_code != NO_CONTENT:
            response = json.loads(response.get_data(as_text=True))
        if error:
            pass
            #self.assertIn('error', response)
            #self.assertEqual(response['error'], error)
        return response

    def get_with_status_check(self, url, status_code=200, error=False, **kwargs):
        return self.__assert_url_access(url, 'get', status_code, error=error, **kwargs)

    def post_with_status_check(self, url, status_code=200, error=False, **kwargs):
        return self.__assert_url_access(url, 'post', status_code, error=error, **kwargs)

    def put_with_status_check(self, url, status_code=200, error=False, **kwargs):
        return self.__assert_url_access(url, 'put', status_code, error=error, **kwargs)

    def patch_with_status_check(self, url, status_code=200, error=False, **kwargs):
        return self.__assert_url_access(url, 'patch', status_code, error=error, **kwargs)

    def delete_with_status_check(self, url, status_code=200, error=False, **kwargs):
        return self.__assert_url_access(url, 'delete', status_code, error=error, **kwargs)
