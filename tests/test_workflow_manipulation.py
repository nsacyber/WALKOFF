import socket
import unittest

import walkoff.appgateway
import walkoff.config
from tests.util import execution_db_help, initialize_test_config
from tests.util.mock_objects import *

from walkoff.executiondb.argument import Argument
from walkoff.multiprocessedexecutor import multiprocessedexecutor
from walkoff.server.app import create_app
from walkoff.executiondb.environment_variable import EnvironmentVariable
from uuid import uuid4
from walkoff.worker.action_exec_strategy import LocalActionExecutionStrategy

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestWorkflowManipulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        execution_db_help.setup_dbs()

        app = create_app(walkoff.config.Config)
        cls.context = app.test_request_context()
        cls.context.push()

        multiprocessedexecutor.MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        multiprocessedexecutor.MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        multiprocessedexecutor.MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        cls.executor = multiprocessedexecutor.MultiprocessedExecutor(
            MockRedisCacheAdapter(),
            LocalActionExecutionStrategy()
        )
        cls.executor.initialize_threading(app)

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

    def test_environment_variables_in_workflow(self):
        workflow = execution_db_help.load_workflow('environmentVariables', 'environmentVariables')

        result = {'value': None}

        def action_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']['data']

        WalkoffEvent.ActionExecutionSuccess.connect(action_finished_listener)

        self.executor.execute_workflow(workflow.id)
        self.executor.wait_and_reset(1)
        self.assertDictEqual(result['value'], {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})

    def test_environment_variables_in_execute(self):
        workflow = execution_db_help.load_workflow('test', 'helloWorldWorkflow')
        env_var = EnvironmentVariable(value='CHANGE INPUT', id=uuid4())
        workflow.actions[0].arguments[0].value = None
        workflow.actions[0].arguments[0].reference = str(env_var.id)

        result = {'value': None}

        def action_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']['data']

        WalkoffEvent.ActionExecutionSuccess.connect(action_finished_listener)

        self.executor.execute_workflow(workflow.id, environment_variables=[env_var])
        self.executor.wait_and_reset(1)
        self.assertDictEqual(result['value'], {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})
