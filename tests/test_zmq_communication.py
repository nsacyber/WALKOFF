import unittest
import time
import socket
from os import path
import apps
import core.controller
import core.config.config
from core.case.callbacks import WorkflowExecutionStart, WorkflowPaused, WorkflowResumed
from core.helpers import import_all_filters, import_all_flags
from tests.util.case_db_help import *
from tests import config
import threading
try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestZMQCommuncation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(config.test_apps_path)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=config.function_api_path)
        core.config.config.num_processes = 2

    def setUp(self):
        self.controller = core.controller.controller
        self.controller.workflows = {}
        self.controller.load_playbooks(resource_collection=config.test_workflows_path)
        self.id_tuple = ('simpleDataManipulationWorkflow', 'helloWorldWorkflow')
        self.testWorkflow = self.controller.get_workflow(*self.id_tuple)
        self.testWorkflow.set_execution_uid('some_uid')
        self.start = datetime.utcnow()
        self.controller.initialize_threading()
        case_database.initialize()

    def tearDown(self):
        self.controller.workflows = None
        case_database.case_db.tear_down()
        case_subscription.clear_subscriptions()
        reload(socket)

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    '''Request and Result Socket Testing (Basic Workflow Execution)'''

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
        self.assertDictEqual(result['result'], {'result': "REPEATING: Hello World", 'status': 'Success'})

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
        for result in [step['data']['result'] for step in steps]:
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
        for result in [step['data']['result'] for step in steps]:
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
        for result in [step['data']['result'] for step in steps]:
            self.assertIn(result, expected_results)

    '''Communication Socket Testing'''

    def test_pause_and_resume_workflow(self):
        self.controller.load_playbook(resource=path.join(config.test_workflows_path, 'pauseWorkflowTest.playbook'))

        uid = None
        result = dict()
        result['paused'] = False
        result['resumed'] = False

        @WorkflowPaused.connect
        def workflow_paused_listener(sender, **kwargs):
            result['paused'] = True
            self.controller.resume_workflow('pauseWorkflowTest', 'pauseWorkflow', uid)

        @WorkflowResumed.connect
        def workflow_resumed_listener(sender, **kwargs):
            result['resumed'] = True

        def pause_resume_thread():
            self.controller.pause_workflow('pauseWorkflowTest', 'pauseWorkflow', uid)
            return

        @WorkflowExecutionStart.connect
        def step_1_about_to_begin_listener(sender, **kwargs):
            threading.Thread(target=pause_resume_thread).start()
            time.sleep(0)

        uid = self.controller.execute_workflow('pauseWorkflowTest', 'pauseWorkflow')
        self.controller.shutdown_pool(1)
        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])
