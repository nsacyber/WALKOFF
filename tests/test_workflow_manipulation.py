import socket
import unittest

from mock import create_autospec

import walkoff.appgateway
import walkoff.config
from tests import config
from tests.util import execution_db_help
from tests.util.mock_objects import *
from walkoff.case.logger import CaseLogger
from walkoff.executiondb.argument import Argument
from walkoff.multiprocessedexecutor import multiprocessedexecutor

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestWorkflowManipulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.config.initialize(config)
        execution_db_help.setup_dbs()

        from flask import current_app
        cls.context = current_app.test_request_context()
        cls.context.push()

        from walkoff.server import context
        current_app.running_context = context.Context(walkoff.config.Config)

        multiprocessedexecutor.MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        multiprocessedexecutor.MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        multiprocessedexecutor.MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        cls.executor = multiprocessedexecutor.MultiprocessedExecutor(
            MockRedisCacheAdapter(),
            create_autospec(CaseLogger))
        cls.executor.initialize_threading(walkoff.config.Config.ZMQ_PUBLIC_KEYS_PATH,
                                          walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH,
                                          walkoff.config.Config.ZMQ_RESULTS_ADDRESS,
                                          walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS)

    def tearDown(self):
        execution_db_help.cleanup_execution_db()
        reload(socket)

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        cls.executor.shutdown_pool()
        execution_db_help.tear_down_execution_db()

    def test_change_action_input(self):
        arguments = [Argument(name='call', value='CHANGE INPUT')]

        result = {'value': None}

        def action_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']['data']

        WalkoffEvent.ActionExecutionSuccess.connect(action_finished_listener)

        workflow = execution_db_help.load_workflow('simpleDataManipulationWorkflow', 'helloWorldWorkflow')

        self.executor.execute_workflow(workflow.id, start_arguments=arguments)
        self.executor.wait_and_reset(1)
        self.assertDictEqual(
            result['value'],
            {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})
