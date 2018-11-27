import os
import shutil
import stat
import unittest

import walkoff.appgateway
import walkoff.config
from start_workers import spawn_worker_processes
from tests.util import execution_db_help, initialize_test_config
from tests.util.mock_objects import *
from walkoff.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from walkoff.server.app import create_app
from walkoff.server.blueprints.root import create_user

if not getattr(__builtins__, 'WindowsError', None):
    class WindowsError(OSError): pass


class ServerTestCase(unittest.TestCase):
    patch = True

    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        cls.conf = walkoff.config.Config

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

        if (cls.conf.DATA_DIR_NAME not in os.listdir(cls.conf.TEST_PATH)
                or os.path.isfile(cls.conf.DATA_PATH)):
            if os.path.isfile(cls.conf.DATA_PATH):
                os.remove(cls.conf.DATA_PATH)
            os.makedirs(cls.conf.DATA_PATH)

        cls.app = create_app()
        cls.app.testing = True
        cls.context = cls.app.test_request_context()
        cls.context.push()

        create_user()

        if cls.patch:
            MultiprocessedExecutor.initialize_threading = mock_initialize_threading
            MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
            MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
            cls.app.running_context.executor.initialize_threading(cls.app)
        else:
            walkoff.config.Config.write_values_to_file()
            pids = spawn_worker_processes()
            cls.app.running_context.executor.initialize_threading(cls.app, pids)

    @classmethod
    def tearDownClass(cls):
        if cls.conf.DATA_PATH in os.listdir(cls.conf.TEST_PATH):
            if os.path.isfile(cls.conf.DATA_PATH):
                os.remove(cls.conf.DATA_PATH)
            else:
                shutil.rmtree(cls.conf.DATA_PATH)

        cls.app.running_context.executor.shutdown_pool()

        execution_db_help.cleanup_execution_db()
        execution_db_help.tear_down_execution_db()

        walkoff.appgateway.clear_cache()

    def setUp(self):
        self.test_client = self.app.test_client(self)

        post = self.test_client.post('/api/auth', content_type="application/json",
                                     data=json.dumps(dict(username='admin', password='admin')), follow_redirects=True)
        key = json.loads(post.get_data(as_text=True))
        print(key)
        self.headers = {'Authorization': 'Bearer {}'.format(key['access_token'])}
        self.http_verb_lookup = {'get': self.test_client.get,
                                 'post': self.test_client.post,
                                 'put': self.test_client.put,
                                 'delete': self.test_client.delete,
                                 'patch': self.test_client.patch}

    def tearDown(self):
        execution_db_help.cleanup_execution_db()

        for data_file in os.listdir(self.conf.DATA_PATH):
            try:
                os.remove(os.path.join(self.conf.DATA_PATH, data_file))
            except WindowsError:  # Windows sometimes makes files read only when created
                os.chmod(os.path.join(self.conf.DATA_PATH, data_file), stat.S_IWRITE)
                os.remove(os.path.join(self.conf.DATA_PATH, data_file))

    def preTearDown(self):
        """
        If overridden, this function is run before ServerTestCase.tearDown is run
        :return: None
        """
        pass

    def __assert_url_access(self, url, method, status_code, error, **kwargs):
        from walkoff.server.returncodes import NO_CONTENT

        try:
            response = self.http_verb_lookup[method.lower()](url, **kwargs)
        except KeyError:
            import traceback
            traceback.print_exc()
            traceback.print_stack()
            raise ValueError('method must be either get, put, post, patch, or delete')
        self.assertEqual(response.status_code, status_code)
        if status_code != NO_CONTENT:
            response = json.loads(response.get_data(as_text=True))
        if error:
            pass
            # self.assertIn('error', response)
            # self.assertEqual(response['error'], error)
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
