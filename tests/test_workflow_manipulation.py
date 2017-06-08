import ast
import unittest
from datetime import datetime
import gevent
from gevent.event import Event
from os import path
from core import controller
from core.step import Step
from core.instance import Instance
from core.config.config import initialize
import core.case.database as case_database
import core.case.subscription as case_subscription
from core.case.callbacks import FunctionExecutionSuccess, StepInputValidated
from core.helpers import construct_workflow_name_key
from tests import config
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
from core.controller import _WorkflowKey
from server import flaskserver as flask_server
from server.flaskserver import running_context
from timeit import default_timer
import json


class TestWorkflowManipulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize()

    def setUp(self):
        case_database.initialize()
        self.app = flask_server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        self.c = controller.Controller(
            workflows_path=path.join(".", "tests", "testWorkflows", "testGeneratedWorkflows"))
        self.c.load_workflows_from_file(
            path=path.join(config.test_workflows_path, 'simpleDataManipulationWorkflow.workflow'))
        self.id_tuple = ('simpleDataManipulationWorkflow', 'helloWorldWorkflow')
        self.workflow_name = construct_workflow_name_key(*self.id_tuple)
        self.testWorkflow = self.c.get_workflow(*self.id_tuple)

    def tearDown(self):
        self.c.workflows = None
        case_database.case_db.tear_down()
        case_subscription.clear_subscriptions()

    def __execution_test(self):
        running_context.init_threads()
        step_names = ['start', '1']
        setup_subscriptions_for_step(self.testWorkflow.name, step_names)
        start = datetime.utcnow()
        # Check that the workflow executed correctly post-manipulation
        self.c.execute_workflow(*self.id_tuple)

        with flask_server.running_context.flask_app.app_context():
            flask_server.running_context.shutdown_threads()

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
        self.assertEqual(len(self.c.workflows), 2)
        # Create Empty Workflow
        self.c.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.assertEqual(len(self.c.workflows), 3)
        self.assertEqual(self.c.get_workflow('emptyWorkflow', 'emptyWorkflow').steps, {})

        xml = self.c.get_workflow('emptyWorkflow', 'emptyWorkflow').to_xml()
        self.assertEqual(len(xml.findall(".//steps/*")), 0)

    def test_remove_workflow(self):
        initial_workflows = list(self.c.workflows.keys())
        self.c.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.assertEqual(len(self.c.workflows), 3)
        success = self.c.remove_workflow('emptyWorkflow', 'emptyWorkflow')
        self.assertTrue(success)
        self.assertEqual(len(self.c.workflows), 2)
        key = _WorkflowKey('emptyWorkflow', 'emptyWorkflow')
        self.assertNotIn(key, self.c.workflows)
        orderless_list_compare(self, list(self.c.workflows.keys()), initial_workflows)

    def test_update_workflow(self):
        self.c.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.c.update_workflow_name('emptyWorkflow', 'emptyWorkflow', 'newPlaybookName', 'newWorkflowName')
        old_key = _WorkflowKey('emptyWorkflow', 'emptyWorkflow')
        new_key = _WorkflowKey('newPlaybookName', 'newWorkflowName')
        self.assertEqual(len(self.c.workflows), 3)
        self.assertNotIn(old_key, self.c.workflows)
        self.assertIn(new_key, self.c.workflows)

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
        self.c.load_workflows_from_file(path=path.join(config.test_workflows_path, 'multiactionWorkflowTest.workflow'))
        workflow = self.c.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        original_steps = {step_name: step.as_json() for step_name, step in workflow.steps.items()}
        cytoscape_data = workflow.get_cytoscape_data()
        workflow.steps = {}
        workflow.from_cytoscape_data(cytoscape_data)
        derived_steps = {step_name: step.as_json() for step_name, step in workflow.steps.items()}
        self.assertDictEqual(derived_steps, original_steps)

    def test_name_parent_rename(self):
        workflow = controller.wf.Workflow(parent_name='workflow_parent', name='workflow')
        new_ancestry = ['workflow_parent_update']
        workflow.reconstruct_ancestry(new_ancestry)
        new_ancestry.append('workflow')
        self.assertListEqual(new_ancestry, workflow.ancestry)

    def test_name_parent_step_rename(self):
        workflow = controller.wf.Workflow(parent_name='workflow_parent', name='workflow')
        step = Step(name="test_step", ancestry=workflow.ancestry)
        workflow.steps["test_step"] = step

        new_ancestry = ["workflow_parent_update"]
        workflow.reconstruct_ancestry(new_ancestry)
        new_ancestry.append("workflow")
        new_ancestry.append("test_step")
        self.assertListEqual(new_ancestry, workflow.steps["test_step"].ancestry)

    def test_name_parent_multiple_step_rename(self):
        workflow = controller.wf.Workflow(parent_name='workflow_parent', name='workflow')
        step_one = Step(name="test_step_one", ancestry=workflow.ancestry)
        step_two = Step(name="test_step_two", ancestry=workflow.ancestry)
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
        workflow = controller.wf.Workflow(name='workflow')
        workflow.create_step(name="stepOne", risk=1)
        workflow.create_step(name="stepTwo", risk=2)
        workflow.create_step(name="stepThree", risk=3)

        self.assertEqual(workflow.total_risk, 6)

    def test_accumulated_risk_with_error(self):
        workflow = controller.wf.Workflow(name='workflow')

        workflow.create_step(name="stepOne", app='HelloWorld', action='helloWorld', risk=1)
        workflow.steps["stepOne"].inputs = {'call': {'key': 'call', 'value': 'HelloWorld', 'format':'str'}}

        workflow.create_step(name="stepTwo", app='HelloWorld', action='repeatBackToMe', risk=2)
        workflow.steps["stepTwo"].inputs = {'number': {'key': 'number', 'value': '6', 'format': 'str'}}

        workflow.create_step(name="stepThree", app='HelloWorld', action='returnPlusOne', risk=3)
        workflow.steps["stepThree"].inputs = {}

        instance = Instance.create(app_name='HelloWorld', device_name='test_device_name')

        workflow._Workflow__execute_step(workflow.steps["stepOne"], instance=instance())
        self.assertEqual(workflow.accumulated_risk, 1.0 / 6.0)
        workflow._Workflow__execute_step(workflow.steps["stepTwo"], instance=instance())
        self.assertEqual(workflow.accumulated_risk, (1.0 / 6.0) + (2.0 / 6.0))
        workflow._Workflow__execute_step(workflow.steps["stepThree"], instance=instance())
        self.assertEqual(workflow.accumulated_risk, 1.0)

    def test_pause_and_resume_workflow(self):
        self.c.load_workflows_from_file(path=path.join(config.test_workflows_path, 'pauseWorkflowTest.workflow'))

        waiter = Event()

        def step_2_finished_listener(sender, **kwargs):
            if sender.name == '2':
                waiter.set()

        def pause_resume_thread():
            uuid = self.c.pause_workflow('pauseWorkflowTest', 'pauseWorkflow')
            gevent.sleep(1.5)
            self.c.resume_workflow('pauseWorkflowTest', 'pauseWorkflow', uuid)

        def step_1_about_to_begin_listener(sender, **kwargs):
            if sender.name == '1':
                gevent.spawn(pause_resume_thread)

        FunctionExecutionSuccess.connect(step_2_finished_listener)
        StepInputValidated.connect(step_1_about_to_begin_listener)

        start = default_timer()
        self.c.execute_workflow('pauseWorkflowTest', 'pauseWorkflow')
        waiter.wait(timeout=5)
        duration = default_timer() - start
        self.assertTrue(2.5 < duration < 5)

    def test_pause_and_resume_workflow_breakpoint(self):
        self.c.load_workflows_from_file(path=path.join(config.test_workflows_path, 'pauseWorkflowTest.workflow'))

        waiter = Event()

        def step_2_finished_listener(sender, **kwargs):
            if sender.name == '2':
                waiter.set()

        def pause_resume_thread():
            self.c.add_workflow_breakpoint_steps('pauseWorkflowTest', 'pauseWorkflow', ['2'])
            gevent.sleep(1.5)
            self.c.resume_breakpoint_step('pauseWorkflowTest', 'pauseWorkflow')

        def step_1_about_to_begin_listener(sender, **kwargs):
            if sender.name == '1':
                gevent.spawn(pause_resume_thread)

        FunctionExecutionSuccess.connect(step_2_finished_listener)
        StepInputValidated.connect(step_1_about_to_begin_listener)

        start = default_timer()
        self.c.execute_workflow('pauseWorkflowTest', 'pauseWorkflow')
        waiter.wait(timeout=5)
        duration = default_timer() - start
        self.assertTrue(2.5 < duration < 5)

    def test_change_step_input(self):

        input = [{"key":"call", "value":"CHANGE INPUT"}]

        input_arg = {arg['key']: {'key':arg['key'],
                                      'value':arg['value'],
                                      'format':arg.get('format', 'str')}
                 for arg in input}

        result = {'value': None}

        def step_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        FunctionExecutionSuccess.connect(step_finished_listener)

        self.testWorkflow.execute(start_input=input_arg)
        self.assertDictEqual(json.loads(result['value']), {"result": "REPEATING: CHANGE INPUT"})
