import unittest

import core.config.config
import core.controller
import core.loadbalancer
import core.multiprocessedexecutor
from core.case import database
from core.case import subscription
from tests import config
from tests.util.case_db_help import *
from tests.util.mock_objects import *


class TestSimpleWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from apps import cache_apps
        cache_apps(path=config.test_apps_path)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.num_processes = 2
        core.multiprocessedexecutor.MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        core.multiprocessedexecutor.MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool

    def setUp(self):
        self.controller = core.controller.controller
        self.controller.workflows = {}
        self.controller.load_playbooks(resource_collection=config.test_workflows_path)
        self.start = datetime.utcnow()

        self.controller.initialize_threading()
        database.initialize()

    def tearDown(self):
        database.case_db.tear_down()
        subscription.clear_subscriptions()

    @classmethod
    def tearDownClass(cls):
        import apps
        apps.clear_cache()

    def test_simple_workflow_execution(self):
        workflow = self.controller.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        step_uids = [step.uid for step in workflow.steps.values() if step.name == 'start']
        setup_subscriptions_for_step(workflow.uid, step_uids)
        self.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.controller.shutdown_pool(1)

        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, self.start, datetime.utcnow()))

        self.assertEqual(len(steps), 1)
        step = steps[0]
        result = step['data']
        self.assertDictEqual(result, {'result': "REPEATING: Hello World", 'status': 'Success'})

    def test_multi_action_workflow(self):
        workflow = self.controller.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        step_names = ['start', '1']
        step_uids = [step.uid for step in workflow.steps.values() if step.name in step_names]
        setup_subscriptions_for_step(workflow.uid, step_uids)
        self.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

        self.controller.shutdown_pool(1)
        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, self.start, datetime.utcnow()))

        self.assertEqual(len(steps), 2)
        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'result': "REPEATING: Hello World", 'status': 'Success'}]
        for result in [step['data'] for step in steps]:
            self.assertIn(result, expected_results)

    def test_error_workflow(self):
        workflow = self.controller.get_workflow('multistepError', 'multiactionErrorWorkflow')
        step_names = ['start', '1', 'error']
        step_uids = [step.uid for step in workflow.steps.values() if step.name in step_names]
        setup_subscriptions_for_step(workflow.uid, step_uids)
        self.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')

        self.controller.shutdown_pool(1)

        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(steps), 2)

        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'status': 'Success', 'result': 'REPEATING: Hello World'}]
        for result in [step['data'] for step in steps]:
            self.assertIn(result, expected_results)

    def test_workflow_with_dataflow(self):
        workflow = self.controller.get_workflow('dataflowTest', 'dataflowWorkflow')
        step_names = ['start', '1', '2']
        step_uids = [step.uid for step in workflow.steps.values() if step.name in step_names]
        setup_subscriptions_for_step(workflow.uid, step_uids)
        self.controller.execute_workflow('dataflowTest', 'dataflowWorkflow')

        self.controller.shutdown_pool(1)

        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(steps), 3)
        expected_results = [{'result': 6, 'status': 'Success'},
                            {'result': 6, 'status': 'Success'},
                            {'result': 15, 'status': 'Success'}]
        for result in [step['data'] for step in steps]:
            self.assertIn(result, expected_results)

    def test_workflow_with_dataflow_step_not_executed(self):
        workflow = self.controller.get_workflow('dataflowTest', 'dataflowWorkflow')
        step_names = ['start', '1']
        step_uids = [step.uid for step in workflow.steps.values() if step.name in step_names]
        setup_subscriptions_for_step(workflow.uid, step_uids)
        self.controller.execute_workflow('dataflowTest', 'dataflowWorkflow')

        self.controller.shutdown_pool(1)

        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(steps), 2)
