import os
import shutil
import stat
import unittest

import tests.config
import walkoff.appgateway
import walkoff.config
from tests.util import execution_db_help
from tests.util.mock_objects import *
from tests.util.thread_control import *
from walkoff.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor

if not getattr(__builtins__, 'WindowsError', None):
    class WindowsError(OSError): pass


class ServerTestCase(unittest.TestCase):
    patch = True

    @classmethod
    def setUpClass(cls):
        walkoff.config.Config.load_config(config_path=tests.config.TEST_CONFIG_PATH)
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

        cls.execution_db, cls.case_db = execution_db_help.setup_dbs()

        walkoff.appgateway.clear_cache()
        walkoff.appgateway.cache_apps(path=cls.conf.APPS_PATH)
        walkoff.config.app_apis = {}
        walkoff.config.load_app_apis(apps_path=cls.conf.APPS_PATH)

        from walkoff.server import flaskserver
        cls.context = flaskserver.app.test_request_context()
        cls.context.push()

        from walkoff.server import context
        flaskserver.app.running_context = context.Context(walkoff.config.Config)
        cls.execution_db = flaskserver.app.running_context.execution_db
        cls.case_db = flaskserver.app.running_context.case_db

        from walkoff.server.app import create_user
        create_user()
        if cls.patch:
            MultiprocessedExecutor.initialize_threading = mock_initialize_threading
            MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
            MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
            flaskserver.app.running_context.executor.initialize_threading(cls.conf.ZMQ_PUBLIC_KEYS_PATH,
                                                                      cls.conf.ZMQ_PRIVATE_KEYS_PATH,
                                                                      cls.conf.ZMQ_RESULTS_ADDRESS,
                                                                      cls.conf.ZMQ_COMMUNICATION_ADDRESS)
        else:
            from walkoff.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
            pids = spawn_worker_processes(cls.conf.NUMBER_PROCESSES, cls.conf.NUMBER_THREADS_PER_PROCESS,
                                          cls.conf.ZMQ_PRIVATE_KEYS_PATH, cls.conf.ZMQ_RESULTS_ADDRESS,
                                          cls.conf.ZMQ_COMMUNICATION_ADDRESS,
                                          worker_environment_setup=modified_setup_worker_env)
            flaskserver.app.running_context.executor.initialize_threading(cls.conf.ZMQ_PUBLIC_KEYS_PATH,
                                                                      cls.conf.ZMQ_PRIVATE_KEYS_PATH,
                                                                      cls.conf.ZMQ_RESULTS_ADDRESS,
                                                                      cls.conf.ZMQ_COMMUNICATION_ADDRESS,
                                                                      pids)

            from walkoff.cache import make_cache
            cache = make_cache(cls.conf.CACHE)
            flaskserver.app.running_context.executor.cache = cache
            flaskserver.app.running_context.executor.manager.cache = cache

    @classmethod
    def tearDownClass(cls):
        import walkoff.server.flaskserver
        if cls.conf.DATA_PATH in os.listdir(cls.conf.TEST_PATH):
            if os.path.isfile(cls.conf.DATA_PATH):
                os.remove(cls.conf.DATA_PATH)
            else:
                shutil.rmtree(cls.conf.DATA_PATH)

        walkoff.server.flaskserver.app.running_context.executor.shutdown_pool()

        execution_db_help.cleanup_execution_db()
        execution_db_help.tear_down_execution_db()

        walkoff.server.flaskserver.app.running_context.case_db.tear_down()
        walkoff.appgateway.clear_cache()
        walkoff.config.Config.load_config()

    def setUp(self):
        import walkoff.server.flaskserver

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
        import walkoff.server.flaskserver
        walkoff.server.flaskserver.app.running_context.execution_db.session.rollback()

        for data_file in os.listdir(self.conf.DATA_PATH):
            try:
                os.remove(os.path.join(self.conf.DATA_PATH, data_file))
            except WindowsError as we:  # Windows sometimes makes files read only when created
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
