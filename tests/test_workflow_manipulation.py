import unittest
import time
import socket
from os import path
import core.controller
from core.workflow import Workflow
from core.step import Step
from core.instance import Instance
import core.config.config
import core.case.database as case_database
import core.case.subscription as case_subscription
from core.case.callbacks import FunctionExecutionSuccess, WorkflowExecutionStart, WorkflowPaused, WorkflowResumed
from core.helpers import import_all_apps, import_all_filters, import_all_flags
from tests import config
from tests.apps import App
from tests.util.assertwrappers import orderless_list_compare
from core.controller import _WorkflowKey
from tests.util.thread_control import *
import core.load_balancer
import threading

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestWorkflowManipulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        App.registry = {}
        import_all_apps(path=config.test_apps_path, reload=True)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=config.function_api_path)
        core.config.config.num_processes = 2
        core.load_balancer.Worker.setup_worker_env = modified_setup_worker_env

    def setUp(self):
        self.controller = core.controller.controller
        self.controller.workflows = {}
        self.controller.load_all_workflows_from_directory(path=path.join(".", "tests", "testWorkflows", "testGeneratedWorkflows"))
        self.controller.load_workflows_from_file(
            path=path.join(config.test_workflows_path, 'simpleDataManipulationWorkflow.playbook'))
        self.id_tuple = ('simpleDataManipulationWorkflow', 'helloWorldWorkflow')
        self.testWorkflow = self.controller.get_workflow(*self.id_tuple)
        self.testWorkflow.execution_uid = 'some_uid'
        case_database.initialize()

    def tearDown(self):
        self.controller.workflows = None
        case_database.case_db.tear_down()
        case_subscription.clear_subscriptions()
        self.controller.shutdown_pool(0)
        reload(socket)
    """
        CRUD - Workflow
    """

    def test_create_workflow(self):
        self.assertEqual(len(self.controller.workflows), 2)
        # Create Empty Workflow
        self.controller.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.assertEqual(len(self.controller.workflows), 3)
        self.assertEqual(self.controller.get_workflow('emptyWorkflow', 'emptyWorkflow').steps, {})

        json = self.controller.get_workflow('emptyWorkflow', 'emptyWorkflow').as_json()
        self.assertEqual(len(json['steps']), 0)

    def test_remove_workflow(self):
        initial_workflows = list(self.controller.workflows.keys())
        self.controller.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.assertEqual(len(self.controller.workflows), 3)
        success = self.controller.remove_workflow('emptyWorkflow', 'emptyWorkflow')
        self.assertTrue(success)
        self.assertEqual(len(self.controller.workflows), 2)
        key = _WorkflowKey('emptyWorkflow', 'emptyWorkflow')
        self.assertNotIn(key, self.controller.workflows)
        orderless_list_compare(self, list(self.controller.workflows.keys()), initial_workflows)

    def test_update_workflow(self):
        self.controller.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.controller.update_workflow_name('emptyWorkflow', 'emptyWorkflow', 'newPlaybookName', 'newWorkflowName')
        old_key = _WorkflowKey('emptyWorkflow', 'emptyWorkflow')
        new_key = _WorkflowKey('newPlaybookName', 'newWorkflowName')
        self.assertEqual(len(self.controller.workflows), 3)
        self.assertNotIn(old_key, self.controller.workflows)
        self.assertIn(new_key, self.controller.workflows)

    def test_display_workflow(self):
        workflow = self.testWorkflow.as_json()
        self.assertEqual(len(workflow["steps"]), 1)

    def test_simple_risk(self):
        workflow = Workflow(name='workflow')
        workflow.create_step(name="stepOne", action='helloWorld', app='HelloWorld', risk=1)
        workflow.create_step(name="stepTwo", action='helloWorld', app='HelloWorld', risk=2)
        workflow.create_step(name="stepThree", action='helloWorld', app='HelloWorld', risk=3)

        self.assertEqual(workflow.total_risk, 6)

    def test_accumulated_risk_with_error(self):
        workflow = Workflow(name='workflow')
        workflow.execution_uid = 'some_uid'
        step1 = Step(name="step_one", app='HelloWorld', action='Buggy', risk=1)
        step2 = Step(name="step_two", app='HelloWorld', action='Buggy', risk=2)
        step3 = Step(name="step_three", app='HelloWorld', action='Buggy', risk=3.5)
        workflow.steps = {'step_one': step1, 'step_two': step2, 'step_three': step3}
        workflow.total_risk = 6.5

        instance = Instance.create(app_name='HelloWorld', device_name='test_device_name')

        workflow._Workflow__execute_step(workflow.steps["step_one"], instance)
        self.assertAlmostEqual(workflow.accumulated_risk, 1.0 / 6.5)
        workflow._Workflow__execute_step(workflow.steps["step_two"], instance)
        self.assertAlmostEqual(workflow.accumulated_risk, (1.0 / 6.5) + (2.0 / 6.5))
        workflow._Workflow__execute_step(workflow.steps["step_three"], instance)
        self.assertAlmostEqual(workflow.accumulated_risk, 1.0)

    def test_pause_and_resume_workflow(self):
        self.controller.initialize_threading()
        self.controller.load_workflows_from_file(path=path.join(config.test_workflows_path, 'pauseWorkflowTest.playbook'))

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

    def test_pause_and_resume_workflow_breakpoint(self):
        self.controller.initialize_threading()
        self.controller.load_workflows_from_file(path=path.join(config.test_workflows_path, 'pauseWorkflowTest.playbook'))
        self.controller.add_workflow_breakpoint_steps('pauseWorkflowTest', 'pauseWorkflow', ['2'])

        uid = None
        result = dict()
        result['paused'] = False
        result['resumed'] = False

        @WorkflowPaused.connect
        def workflow_paused_listener(sender, **kwargs):
            result['paused'] = True
            self.controller.resume_breakpoint_step('pauseWorkflowTest', 'pauseWorkflow', uid)

        @WorkflowResumed.connect
        def workflow_resumed_listener(sender, **kwargs):
            result['resumed'] = True

        uid = self.controller.execute_workflow('pauseWorkflowTest', 'pauseWorkflow')
        self.controller.shutdown_pool(1)
        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])

    def test_change_step_input(self):
        self.controller.initialize_threading()
        input_list = [{'key': 'call', 'value': 'CHANGE INPUT'}]

        input_arg = {arg['key']: arg['value'] for arg in input_list}

        result = {'value': None}

        def step_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        FunctionExecutionSuccess.connect(step_finished_listener)

        self.controller.execute_workflow('simpleDataManipulationWorkflow', 'helloWorldWorkflow', start_input=input_arg)
        self.controller.shutdown_pool(1)
        self.assertDictEqual(result['value'],
                             {'result': {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'}})
