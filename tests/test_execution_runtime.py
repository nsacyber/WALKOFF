import unittest
from datetime import datetime

import walkoff.appgateway
import walkoff.case.database as case_database
import walkoff.config.config
import walkoff.config.config
import walkoff.controller
from walkoff.case import subscription
from walkoff.core.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from tests import config
from tests.util.case_db_help import executed_actions, setup_subscriptions_for_action
from tests.util.mock_objects import *
import walkoff.config.paths
import tests.config
from walkoff import initialize_databases


class TestExecutionRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.config.paths.db_path = tests.config.test_db_path
        walkoff.config.paths.case_db_path = tests.config.test_case_db_path
        walkoff.config.paths.device_db_path = tests.config.test_device_db_path
        initialize_databases()
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        walkoff.controller.controller.initialize_threading()

    def setUp(self):
        self.start = datetime.utcnow()
        case_database.initialize()
        self.controller = walkoff.controller.controller
        self.controller.workflows = {}
        # self.controller.load_playbooks(resource_collection=config.test_workflows_path)

    def tearDown(self):
        subscription.clear_subscriptions()

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        walkoff.controller.controller.shutdown_pool()

    def test_templated_workflow(self):
        action_names = ['start', '1']

        workflow = self.controller.get_workflow('templatedWorkflowTest', 'templatedWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name in action_names]
        setup_subscriptions_for_action(workflow.id, action_ids)
        self.controller.execute_workflow('templatedWorkflowTest', 'templatedWorkflow')

        self.controller.wait_and_reset(1)

        actions = []
        for uid in action_ids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 2, 'Unexpected number of actions executed. '
                                          'Expected {0}, got {1}'.format(2, len(actions)))

        # def test_simple_tiered_workflow(self):
        #     workflow1 = self.controller.get_workflow('tieredWorkflow', 'parentWorkflow')
        #     workflow2 = self.controller.get_workflow('tieredWorkflow', 'childWorkflow')
        #     action_names = ['start', '1']
        #     action_ids = [action.uid for action in workflow1.actions.values() if action.name in action_names]
        #     action_ids.extend([action.uid for action in workflow2.actions.values() if action.name in action_names])
        #     setup_subscriptions_for_action([workflow1.uid, workflow2.uid], action_ids)
        #     self.controller.execute_workflow('tieredWorkflow', 'parentWorkflow')
        #
        #     self.controller.shutdown_pool(1)
        #     actions = []
        #     for uid in action_ids:
        #         actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
        #     expected_results = [{'status': 'Success', 'result': 'REPEATING: Parent action One'},
        #                         {'status': 'Success', 'result': 'REPEATING: Child action One'},
        #                         {'status': 'Success', 'result': 'REPEATING: Parent action Two'}]
        #     self.assertEqual(len(actions), 3)
        #     for result in [action['data']['result'] for action in actions]:
        #         self.assertIn(result, expected_results)
        #
        # def test_loop(self):
        #     from gevent import monkey
        #     from gevent.event import Event
        #     from core.case.callbacks import WorkflowShutdown
        #     monkey.patch_all()
        #
        #     workflow = self.controller.get_workflow('loopWorkflow', 'loopWorkflow')
        #     action_names = ['start', '1']
        #     action_ids = [action.uid for action in workflow.actions.values() if action.name in action_names]
        #     setup_subscriptions_for_action(workflow.uid, action_ids)
        #
        #     waiter = Event()
        #
        #     def wait_for_shutdown(sender, **kwargs):
        #         waiter.set()
        #
        #     WorkflowShutdown.connect(wait_for_shutdown)
        #     self.controller.execute_workflow('loopWorkflow', 'loopWorkflow')
        #     self.controller.shutdown_pool(1)
        #     actions = []
        #     for uid in action_ids:
        #         actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
        #
        #     self.assertEqual(len(actions), 5)
