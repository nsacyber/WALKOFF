import unittest

import walkoff.config.config
import walkoff.core.controller
from walkoff.case import subscription, database
from walkoff.core.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from tests import config
from tests.util.case_db_help import *
from tests.util.mock_objects import *


class TestSimpleWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from apps import cache_apps
        cache_apps(path=config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        walkoff.config.config.num_processes = 2
        MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        walkoff.core.controller.controller.initialize_threading()

    def setUp(self):
        self.controller = walkoff.core.controller.controller
        self.controller.workflows = {}
        self.controller.load_playbooks(resource_collection=config.test_workflows_path)
        self.start = datetime.utcnow()

        database.initialize()

    def tearDown(self):
        database.case_db.tear_down()
        subscription.clear_subscriptions()

    @classmethod
    def tearDownClass(cls):
        import apps
        apps.clear_cache()
        walkoff.core.controller.controller.shutdown_pool()

    def test_simple_workflow_execution(self):
        workflow = self.controller.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
        setup_subscriptions_for_action(workflow.uid, action_uids)
        self.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.controller.wait_and_reset(1)

        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 1)
        action = actions[0]
        result = action['data']
        self.assertDictEqual(result, {'result': "REPEATING: Hello World", 'status': 'Success'})

    def test_multi_action_workflow(self):
        workflow = self.controller.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        action_names = ['start', '1']
        action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
        setup_subscriptions_for_action(workflow.uid, action_uids)
        self.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

        self.controller.wait_and_reset(1)
        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 2)
        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'result': "REPEATING: Hello World", 'status': 'Success'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_error_workflow(self):
        workflow = self.controller.get_workflow('multiactionError', 'multiactionErrorWorkflow')
        action_names = ['start', '1', 'error']
        action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
        setup_subscriptions_for_action(workflow.uid, action_uids)
        self.controller.execute_workflow('multiactionError', 'multiactionErrorWorkflow')

        self.controller.wait_and_reset(1)

        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 2)

        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'status': 'Success', 'result': 'REPEATING: Hello World'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_workflow_with_dataflow(self):
        workflow = self.controller.get_workflow('dataflowTest', 'dataflowWorkflow')
        action_names = ['start', '1', '2']
        action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
        setup_subscriptions_for_action(workflow.uid, action_uids)
        self.controller.execute_workflow('dataflowTest', 'dataflowWorkflow')

        self.controller.wait_and_reset(1)

        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 3)
        expected_results = [{'result': 6, 'status': 'Success'},
                            {'result': 6, 'status': 'Success'},
                            {'result': 15, 'status': 'Success'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_workflow_with_dataflow_action_not_executed(self):
        workflow = self.controller.get_workflow('dataflowTest', 'dataflowWorkflow')
        action_names = ['start', '1']
        action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
        setup_subscriptions_for_action(workflow.uid, action_uids)
        self.controller.execute_workflow('dataflowTest', 'dataflowWorkflow')

        self.controller.wait_and_reset(1)

        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 2)
