import ast
import unittest
import socket
from datetime import datetime
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
from core.helpers import construct_workflow_name_key, import_all_apps, import_all_filters, import_all_flags
from tests import config
from tests.apps import App
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
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
        case_database.initialize()
        self.controller = Controller(workflows_path=path.join(".", "tests", "testWorkflows", "testGeneratedWorkflows"))
        self.controller.load_workflows_from_file(
            path=path.join(config.test_workflows_path, 'simpleDataManipulationWorkflow.playbook'))
        self.id_tuple = ('simpleDataManipulationWorkflow', 'helloWorldWorkflow')
        self.workflow_name = construct_workflow_name_key(*self.id_tuple)
        self.testWorkflow = self.controller.get_workflow(*self.id_tuple)

    def tearDown(self):
        self.controller.workflows = None
        case_database.case_db.tear_down()
        case_subscription.clear_subscriptions()
        reload(socket)

    def __execution_test(self):
        step_names = ['start', '1']
        setup_subscriptions_for_step(self.testWorkflow.name, step_names)
        start = datetime.utcnow()
        # Check that the workflow executed correctly post-manipulation
        self.controller.execute_workflow(*self.id_tuple)

        steps = executed_steps('defaultController', self.testWorkflow.name, start, datetime.utcnow())
        self.assertEqual(len(steps), 2)
        names = [step['ancestry'].split(',')[-1] for step in steps]
        orderless_list_compare(self, names, step_names)
        name_result = {'start': "REPEATING: Hello World",
                       '1': "REPEATING: This is a test."}
        for step in steps:
            name = step['ancestry'].split(',')[-1]
            self.assertIn(name, name_result)
            self.assertEqual(step['data']['result'], name_result[name])

    """
        CRUD - Workflow
    """

    def test_create_workflow(self):
        self.assertEqual(len(self.controller.workflows), 2)
        # Create Empty Workflow
        self.controller.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.assertEqual(len(self.controller.workflows), 3)
        self.assertEqual(self.controller.get_workflow('emptyWorkflow', 'emptyWorkflow').steps, {})

        xml = self.controller.get_workflow('emptyWorkflow', 'emptyWorkflow').to_xml()
        self.assertEqual(len(xml.findall(".//steps/*")), 0)

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
        self.assertTrue(workflow["options"])

    """
        CRUD - Next
    """

    def test_update_next(self):
        step = self.testWorkflow.steps["start"]
        self.assertEqual(step.conditionals[0].name, "1")
        step.conditionals[0].name = "2"
        self.assertEqual(step.conditionals[0].name, "2")

        xml = self.testWorkflow.to_xml()

        # Check XML
        self.assertEqual(xml.find(".//steps/step/[@id='start']/next").get("step"), "2")

    def test_display_next(self):
        conditional = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].__repr__())
        self.assertTrue(conditional["flags"])
        self.assertEqual(conditional["name"], "1")

    def test_to_from_cytoscape_data(self):
        self.controller.load_workflows_from_file(path=path.join(config.test_workflows_path,
                                                                'multiactionWorkflowTest.playbook'))
        workflow = self.controller.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        original_steps = {step_name: step.as_json() for step_name, step in workflow.steps.items()}
        cytoscape_data = workflow.get_cytoscape_data()
        workflow.steps = {}
        workflow.from_cytoscape_data(cytoscape_data)
        derived_steps = {step_name: step.as_json() for step_name, step in workflow.steps.items()}
        self.assertDictEqual(derived_steps, original_steps)

    def test_name_parent_rename(self):
        workflow = Workflow(parent_name='workflow_parent', name='workflow')
        new_ancestry = ['workflow_parent_update']
        workflow.reconstruct_ancestry(new_ancestry)
        new_ancestry.append('workflow')
        self.assertListEqual(new_ancestry, workflow.ancestry)

    def test_name_parent_step_rename(self):
        workflow = Workflow(parent_name='workflow_parent', name='workflow')
        step = Step(name="test_step", action='helloWorld', app='HelloWorld', ancestry=workflow.ancestry)
        workflow.steps["test_step"] = step

        new_ancestry = ["workflow_parent_update"]
        workflow.reconstruct_ancestry(new_ancestry)
        new_ancestry.append("workflow")
        new_ancestry.append("test_step")
        self.assertListEqual(new_ancestry, workflow.steps["test_step"].ancestry)

    def test_name_parent_multiple_step_rename(self):
        workflow = Workflow(parent_name='workflow_parent', name='workflow')
        step_one = Step(name="test_step_one", action='helloWorld', app='HelloWorld', ancestry=workflow.ancestry)
        step_two = Step(name="test_step_two", action='helloWorld', app='HelloWorld', ancestry=workflow.ancestry)
        workflow.steps["test_step_one"] = step_one
        workflow.steps["test_step_two"] = step_two

        new_ancestry = ["workflow_parent_update"]
        workflow.reconstruct_ancestry(new_ancestry)
        new_ancestry.append("workflow")
        new_ancestry.append("test_step_one")
        self.assertListEqual(new_ancestry, workflow.steps["test_step_one"].ancestry)

        new_ancestry.remove("test_step_one")
        new_ancestry.append("test_step_two")
        self.assertListEqual(new_ancestry, workflow.steps["test_step_two"].ancestry)

    def test_simple_risk(self):
        workflow = Workflow(name='workflow')
        workflow.create_step(name="stepOne", action='helloWorld', app='HelloWorld', risk=1)
        workflow.create_step(name="stepTwo", action='helloWorld', app='HelloWorld', risk=2)
        workflow.create_step(name="stepThree", action='helloWorld', app='HelloWorld', risk=3)

        self.assertEqual(workflow.total_risk, 6)

    def test_accumulated_risk_with_error(self):
        workflow = Workflow(name='workflow')
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
        self.controller.load_workflows_from_file(path=path.join(config.test_workflows_path, 'pauseWorkflowTest.playbook'))

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
        self.controller.load_workflows_from_file(path=path.join(config.test_workflows_path, 'pauseWorkflowTest.playbook'))

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

        self.testWorkflow.execute(start_input=input_arg)
        self.assertDictEqual(json.loads(result['value']),
                             {'result': {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'}})
