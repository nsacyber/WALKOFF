import unittest

import walkoff.appgateway
import walkoff.config
import walkoff.server.workflowresults
from tests.util import execution_db_help, initialize_test_config
from tests.util.mock_objects import *
from walkoff.events import WalkoffEvent
from walkoff.multiprocessedexecutor import multiprocessedexecutor
from walkoff.server.app import create_app
from walkoff.worker.action_exec_strategy import LocalActionExecutionStrategy


class TestSimpleWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        execution_db_help.setup_dbs()

        app = create_app()
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

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        cls.executor.shutdown_pool()
        execution_db_help.tear_down_execution_db()

    def assert_execution_event_log(self, playbook, workflow, expected_events):
        events = []

        @WalkoffEvent.CommonWorkflowSignal.connect
        def log_event(sender, **kwargs):
            self.assertIn('event', kwargs)
            events.append(kwargs['event'])

        workflow = execution_db_help.load_workflow(playbook, workflow)
        self.executor.execute_workflow(workflow.id)
        self.executor.wait_and_reset(1)
        self.assertListEqual(events, expected_events)

    def test_simple_workflow_execution(self):
        expected_events = [
            WalkoffEvent.WorkflowExecutionStart,
            WalkoffEvent.AppInstanceCreated,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.WorkflowShutdown]

        self.assert_execution_event_log('basicWorkflowTest', 'helloWorldWorkflow', expected_events)

    def test_multi_action_workflow(self):
        expected_events = [
            WalkoffEvent.WorkflowExecutionStart,
            WalkoffEvent.AppInstanceCreated,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.BranchTaken,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.WorkflowShutdown]

        self.assert_execution_event_log('multiactionWorkflowTest', 'multiactionWorkflow', expected_events)

    def test_error_workflow(self):
        expected_events = [
            WalkoffEvent.WorkflowExecutionStart,
            WalkoffEvent.AppInstanceCreated,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.BranchTaken,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionError,
            WalkoffEvent.BranchTaken,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.WorkflowShutdown]

        self.assert_execution_event_log('multiactionError', 'multiactionErrorWorkflow', expected_events)

    def test_workflow_with_dataflow(self):
        expected_events = [
            WalkoffEvent.WorkflowExecutionStart,
            WalkoffEvent.AppInstanceCreated,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.BranchTaken,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.BranchTaken,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.WorkflowShutdown
        ]

        self.assert_execution_event_log('dataflowTest', 'dataflowWorkflow', expected_events)

    def test_workflow_with_dataflow_action_not_executed(self):
        expected_events = [
            WalkoffEvent.WorkflowExecutionStart,
            WalkoffEvent.AppInstanceCreated,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.BranchTaken,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.BranchTaken,
            WalkoffEvent.ActionStarted,
            WalkoffEvent.ActionExecutionSuccess,
            WalkoffEvent.WorkflowShutdown
        ]

        self.assert_execution_event_log('dataflowTest', 'dataflowWorkflow', expected_events)
