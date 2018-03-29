import unittest

from mock import create_autospec

import walkoff.appgateway
import walkoff.config
from tests import config
from tests.util import execution_db_help
from tests.util.mock_objects import *
from walkoff.case.logger import CaseLogger
from walkoff.events import WalkoffEvent
from walkoff.multiprocessedexecutor import multiprocessedexecutor


class TestSimpleWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()

        from walkoff.appgateway import cache_apps
        cache_apps(path=config.test_apps_path)
        walkoff.config.load_app_apis(apps_path=config.test_apps_path)
        walkoff.config.Config.NUMBER_PROCESSES = 2
        multiprocessedexecutor.MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        multiprocessedexecutor.MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        multiprocessedexecutor.MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        cls.executor = multiprocessedexecutor.MultiprocessedExecutor(MockRedisCacheAdapter(),
                                                                     create_autospec(CaseLogger))
        cls.executor.initialize_threading(walkoff.config.Config.ZMQ_PUBLIC_KEYS_PATH,
                                          walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH,
                                          walkoff.config.Config.ZMQ_RESULTS_ADDRESS,
                                          walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS)

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

<<<<<<< HEAD
    # def test_multi_action_workflow(self):
    #     workflow = execution_db_help.load_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
    #     action_names = ['start', '1']
    #     action_ids = [action_id for action_id, action in workflow.actions.items() if action.name in action_names]
    #     setup_subscriptions_for_action(workflow.id, action_ids)
    #     self.executor.execute_workflow(workflow.id)
    #
    #     self.executor.wait_and_reset(1)
    #     actions = []
    #     for id_ in action_ids:
    #         actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
    #
    #     self.assertEqual(len(actions), 2)
    #     expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
    #                         {'result': "REPEATING: Hello World", 'status': 'Success'}]
    #     for result in [action['data'] for action in actions]:
    #         self.assertIn(result, expected_results)
    #
    # def test_error_workflow(self):
    #     workflow = execution_db_help.load_workflow('multiactionError', 'multiactionErrorWorkflow')
    #     action_names = ['start', '1', 'error']
    #     action_ids = [action_id for action_id, action in workflow.actions.items() if action.name in action_names]
    #     setup_subscriptions_for_action(workflow.id, action_ids)
    #     self.executor.execute_workflow(workflow.id)
    #
    #     self.executor.wait_and_reset(1)
    #
    #     actions = []
    #     for id_ in action_ids:
    #         actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
    #     #print(actions)
    #     self.assertEqual(len(actions), 2)
    #
    #     expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
    #                         {'status': 'Success', 'result': 'REPEATING: Hello World'}]
    #     for result in [action['data'] for action in actions]:
    #         self.assertIn(result, expected_results)
    #
    # def test_workflow_with_dataflow(self):
    #     workflow = execution_db_help.load_workflow('dataflowTest', 'dataflowWorkflow')
    #     action_names = ['start', '1', '2']
    #     action_ids = [action_id for action_id, action in workflow.actions.items() if action.name in action_names]
    #     setup_subscriptions_for_action(workflow.id, action_ids)
    #
    #     self.executor.execute_workflow(workflow.id)
    #
    #     self.executor.wait_and_reset(1)
    #
    #     actions = []
    #     for id_ in action_ids:
    #         actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
    #     self.assertEqual(len(actions), 3)
    #     expected_results = [{'result': 6, 'status': 'Success'},
    #                         {'result': 6, 'status': 'Success'},
    #                         {'result': 15, 'status': 'Success'}]
    #     for result in [action['data'] for action in actions]:
    #         self.assertIn(result, expected_results)
    #
    # def test_workflow_with_dataflow_action_not_executed(self):
    #     workflow = execution_db_help.load_workflow('dataflowTest', 'dataflowWorkflow')
    #     action_names = ['start', '1']
    #     action_ids = [action_id for action_id, action in workflow.actions.items() if action.name in action_names]
    #     setup_subscriptions_for_action(workflow.id, action_ids)
    #     self.executor.execute_workflow(workflow.id)
    #
    #     self.executor.wait_and_reset(1)
    #
    #     actions = []
    #     for id_ in action_ids:
    #         actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
    #     self.assertEqual(len(actions), 2)
=======
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
>>>>>>> development
