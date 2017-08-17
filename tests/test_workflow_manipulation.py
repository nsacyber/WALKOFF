import ast
import unittest
import socket
import gevent
from gevent.event import Event
from os import path
from core.controller import Controller, initialize_threading, shutdown_pool
from core.workflow import Workflow
from core.step import Step
from core.instance import Instance
import core.config.config
import core.case.database as case_database
import core.case.subscription as case_subscription
from core.case.callbacks import FunctionExecutionSuccess, StepInputValidated
from core.helpers import import_all_apps, import_all_filters, import_all_flags
from tests import config
from tests.apps import App
from tests.util.assertwrappers import orderless_list_compare
from core.controller import _WorkflowKey
from timeit import default_timer

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
        initialize_threading()

    @classmethod
    def tearDownClass(cls):
        shutdown_pool()

    def setUp(self):
        self.controller = Controller(workflows_path=path.join(".", "tests", "testWorkflows", "testGeneratedWorkflows"))
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
        workflow = ast.literal_eval(self.testWorkflow.__repr__())
        self.assertEqual(len(workflow["steps"]), 1)
        self.assertIsNone(workflow["options"])

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
        from gevent import monkey
        monkey.patch_all()
        self.controller.load_workflows_from_file(
            path=path.join(config.test_workflows_path, 'pauseWorkflowTest.playbook'))

        waiter = Event()
        uid = None

        def step_2_finished_listener(sender, **kwargs):
            if sender.name == '2':
                waiter.set()

        def pause_resume_thread():
            self.controller.pause_workflow('pauseWorkflowTest', 'pauseWorkflow', uid)
            gevent.sleep(1.5)
            self.controller.resume_workflow('pauseWorkflowTest', 'pauseWorkflow', uid)

        def step_1_about_to_begin_listener(sender, **kwargs):
            if sender.name == '1':
                gevent.spawn(pause_resume_thread)

        FunctionExecutionSuccess.connect(step_2_finished_listener)
        StepInputValidated.connect(step_1_about_to_begin_listener)

        start = default_timer()
        uid = self.controller.execute_workflow('pauseWorkflowTest', 'pauseWorkflow')
        waiter.wait(timeout=5)
        duration = default_timer() - start
        self.assertTrue(2.5 < duration < 5)

    def test_pause_and_resume_workflow_breakpoint(self):
        from gevent import monkey
        monkey.patch_all()
        self.controller.load_workflows_from_file(
            path=path.join(config.test_workflows_path, 'pauseWorkflowTest.playbook'))

        waiter = Event()

        def step_2_finished_listener(sender, **kwargs):
            if sender.name == '2':
                waiter.set()

        def pause_resume_thread():
            self.controller.add_workflow_breakpoint_steps('pauseWorkflowTest', 'pauseWorkflow', ['2'])
            gevent.sleep(1.5)
            self.controller.resume_breakpoint_step('pauseWorkflowTest', 'pauseWorkflow')

        def step_1_about_to_begin_listener(sender, **kwargs):
            if sender.name == '1':
                gevent.spawn(pause_resume_thread)

        FunctionExecutionSuccess.connect(step_2_finished_listener)
        StepInputValidated.connect(step_1_about_to_begin_listener)

        start = default_timer()
        self.controller.execute_workflow('pauseWorkflowTest', 'pauseWorkflow')
        waiter.wait(timeout=5)
        duration = default_timer() - start
        self.assertTrue(2.5 < duration < 5)

    def test_change_step_input(self):
        import json

        input_list = [{'key': 'call', 'value': 'CHANGE INPUT'}]

        input_arg = {arg['key']: arg['value'] for arg in input_list}

        result = {'value': None}

        def step_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        FunctionExecutionSuccess.connect(step_finished_listener)
        self.testWorkflow.execute(start_input=input_arg, execution_uid='some_uid')
        self.assertDictEqual(json.loads(result['value']),
                             {'result': {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'}})
