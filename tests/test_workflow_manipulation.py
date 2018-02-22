import socket
import unittest

import walkoff.appgateway
import walkoff.config.config
from walkoff.multiprocessedexecutor import multiprocessedexecutor
from tests import config
from tests.util.mock_objects import *
import walkoff.config.paths
from tests.util import device_db_help
from walkoff.executiondb.argument import Argument
from tests.util.case_db_help import *

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestWorkflowManipulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        device_db_help.setup_dbs()

        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        walkoff.config.config.num_processes = 2
        multiprocessedexecutor.MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        multiprocessedexecutor.MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        multiprocessedexecutor.MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        multiprocessedexecutor.multiprocessedexecutor.initialize_threading()

    def setUp(self):
        self.start = datetime.utcnow()
        case_database.initialize()

    def tearDown(self):
        device_db_help.cleanup_device_db()
        case_database.case_db.tear_down()
        case_subscription.clear_subscriptions()
        reload(socket)

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        multiprocessedexecutor.multiprocessedexecutor.shutdown_pool()
        device_db_help.tear_down_device_db()

    def test_change_action_input(self):
        arguments = [Argument(name='call', value='CHANGE INPUT')]

        result = {'value': None}

        def action_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        WalkoffEvent.ActionExecutionSuccess.connect(action_finished_listener)

        workflow = device_db_help.load_workflow('simpleDataManipulationWorkflow', 'helloWorldWorkflow')

        multiprocessedexecutor.multiprocessedexecutor.execute_workflow(workflow.id, start_arguments=arguments)
        multiprocessedexecutor.multiprocessedexecutor.wait_and_reset(1)
        self.assertDictEqual(result['value'],
                             {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})
