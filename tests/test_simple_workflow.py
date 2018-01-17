import unittest

import walkoff.appgateway
import walkoff.config.config
import walkoff.controller
from walkoff.case import subscription, database
from walkoff.core.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from tests import config
from tests.util.case_db_help import *
from tests.util.mock_objects import *
import walkoff.config.paths
import tests.config
from walkoff import initialize_databases


class TestSimpleWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.config.paths.db_path = tests.config.test_db_path
        walkoff.config.paths.case_db_path = tests.config.test_case_db_path
        walkoff.config.paths.device_db_path = tests.config.test_device_db_path
        initialize_databases()

        from walkoff.appgateway import cache_apps
        cache_apps(path=config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        walkoff.config.config.num_processes = 2
        MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        walkoff.controller.controller.initialize_threading()

    def setUp(self):
        self.controller = walkoff.controller.controller
        # self.controller.workflows = {}
        # self.controller.load_playbooks(resource_collection=config.test_workflows_path)
        self.start = datetime.utcnow()

        database.initialize()

    def tearDown(self):
        database.case_db.tear_down()
        subscription.clear_subscriptions()

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        walkoff.controller.controller.shutdown_pool()

    def test_simple_workflow_execution(self):
        workflow = self.controller.get_workflow_by_name('basicWorkflowTest', 'helloWorldWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)
        self.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.controller.wait_and_reset(1)

        actions = []
        for uid in action_ids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 1)
        action = actions[0]
        result = action['data']
        self.assertDictEqual(result, {'result': "REPEATING: Hello World", 'status': 'Success'})

    # def test_multi_action_workflow(self):
    #     workflow = self.controller.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
    #     action_names = ['start', '1']
    #     action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
    #     setup_subscriptions_for_action(workflow.uid, action_uids)
    #     self.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
    #
    #     self.controller.wait_and_reset(1)
    #     actions = []
    #     for uid in action_uids:
    #         actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
    #
    #     self.assertEqual(len(actions), 2)
    #     expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
    #                         {'result': "REPEATING: Hello World", 'status': 'Success'}]
    #     for result in [action['data'] for action in actions]:
    #         self.assertIn(result, expected_results)
    #
    # def test_error_workflow(self):
    #     workflow = self.controller.get_workflow('multiactionError', 'multiactionErrorWorkflow')
    #     action_names = ['start', '1', 'error']
    #     action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
    #     setup_subscriptions_for_action(workflow.uid, action_uids)
    #     self.controller.execute_workflow('multiactionError', 'multiactionErrorWorkflow')
    #
    #     self.controller.wait_and_reset(1)
    #
    #     actions = []
    #     for uid in action_uids:
    #         actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
    #     self.assertEqual(len(actions), 2)
    #
    #     expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
    #                         {'status': 'Success', 'result': 'REPEATING: Hello World'}]
    #     for result in [action['data'] for action in actions]:
    #         self.assertIn(result, expected_results)
    #
    # def test_workflow_with_dataflow(self):
    #     workflow = self.controller.get_workflow('dataflowTest', 'dataflowWorkflow')
    #     action_names = ['start', '1', '2']
    #     action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
    #     setup_subscriptions_for_action(workflow.uid, action_uids)
    #     self.controller.execute_workflow('dataflowTest', 'dataflowWorkflow')
    #
    #     self.controller.wait_and_reset(1)
    #
    #     actions = []
    #     for uid in action_uids:
    #         actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
    #     self.assertEqual(len(actions), 3)
    #     expected_results = [{'result': 6, 'status': 'Success'},
    #                         {'result': 6, 'status': 'Success'},
    #                         {'result': 15, 'status': 'Success'}]
    #     for result in [action['data'] for action in actions]:
    #         self.assertIn(result, expected_results)
    #
    # def test_workflow_with_dataflow_action_not_executed(self):
    #     workflow = self.controller.get_workflow('dataflowTest', 'dataflowWorkflow')
    #     action_names = ['start', '1']
    #     action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
    #     setup_subscriptions_for_action(workflow.uid, action_uids)
    #     self.controller.execute_workflow('dataflowTest', 'dataflowWorkflow')
    #
    #     self.controller.wait_and_reset(1)
    #
    #     actions = []
    #     for uid in action_uids:
    #         actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
    #     self.assertEqual(len(actions), 2)
