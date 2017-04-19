import ast
import unittest
from datetime import datetime
from os import path
from core import controller
from core.step import Step, InvalidStepInputError
from core.instance import Instance
from core.arguments import Argument
import core.case.database as case_database
import core.case.subscription as case_subscription
from core.helpers import construct_workflow_name_key
from tests import config
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
from core.controller import _WorkflowKey
from server import flaskserver as flask_server
from server.flaskserver import running_context


class TestWorkflowManipulation(unittest.TestCase):
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
        CRUD - Step
    """

    def test_create_step(self):
        self.testWorkflow.create_step(name="1", action="repeatBackToMe", app="HelloWorld", device="hwTest",
                                      arg_input={"call": {"tag": "call", "value": "This is a test.", "format": "str"}})

        steps = self.testWorkflow.steps

        # Check that the step was added
        self.assertEqual(len(steps), 2)
        self.assertTrue(steps["1"])

        # Check attributes
        step = self.testWorkflow.steps["1"]
        self.assertEqual(step.name, "1")
        self.assertEqual(step.action, "repeatBackToMe")
        self.assertEqual(step.app, "HelloWorld")
        self.assertEqual(step.device, "hwTest")
        # self.assertTrue(step.input == {'call': {'value': 'This is a test.', 'type': 'string', 'key': 'call'}}))
        self.assertEqual(step.conditionals, [])
        self.assertEqual(step.errors, [])

        self.__execution_test()

    def test_add_step_to_xml(self):
        self.testWorkflow.create_step(name="1", action="repeatBackToMe", app="HelloWorld", device="hwTest",
                                      arg_input={"call": {"tag": "call", "value": "This is a test.", "format": "str"}})
        xml = self.testWorkflow.to_xml()

        # Verify Structure
        steps = xml.findall(".//steps/step")
        self.assertEqual(len(steps), 2)
        step = xml.find(".//steps/step/[@id='1']")
        self.assertEqual(step.get("id"), "1")
        self.assertEqual(step.find(".//action").text, "repeatBackToMe")
        self.assertEqual(step.find(".//app").text, "HelloWorld")
        self.assertEqual(step.find(".//device").text, "hwTest")
        self.assertIsNone(step.find(".//next"))
        self.assertIsNone(step.find(".//error"))

        self.__execution_test()

    def test_remove_step(self):
        self.testWorkflow.create_step(name="1", action="repeatBackToMe", app="HelloWorld", device="hwTest",
                                      arg_input={"call": {"tag": "call", "value": "This is a test.", "format": "str"}})
        # Makes sure a new step was created...
        self.assertEqual(len(self.testWorkflow.steps), 2)

        # ...So that we may destroy it!
        removed = self.testWorkflow.remove_step(name="1")
        self.assertTrue(removed)
        self.assertEqual(len(self.testWorkflow.steps), 1)

        # Tests the XML representation after changes
        xml = self.testWorkflow.to_xml()
        steps = xml.findall(".//steps/*")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].get("id"), "start")

    def test_update_step(self):
        self.assertEqual(self.testWorkflow.steps["start"].action, "repeatBackToMe")
        self.testWorkflow.steps["start"].action = "helloWorld"
        self.assertEqual(self.testWorkflow.steps["start"].action, "helloWorld")

        xml = self.testWorkflow.to_xml()
        self.assertEqual(xml.find(".//steps/step/[@id='start']/action").text, "helloWorld")

    def test_display_steps(self):
        output = ast.literal_eval(self.testWorkflow.__repr__())
        self.assertTrue(output["options"])
        self.assertTrue(output["steps"])
        self.assertEqual(len(output["steps"]), 1)
        self.assertEqual(output["steps"]["start"]["action"], "repeatBackToMe")

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

    """
        CRUD - Flag
    """

    def test_create_flag(self):
        next_step = self.testWorkflow.steps["start"].conditionals[0]
        self.assertEqual(len(next_step.flags), 1)
        next_step.create_flag(action="count", args={"operator": "ge", "threshold": "1"}, filters=[])
        self.assertEqual(len(next_step.flags), 2)
        self.assertEqual(next_step.flags[1].action, "count")
        self.assertDictEqual(next_step.flags[1].args, {"operator": "ge", "threshold": "1"})
        self.assertEqual(next_step.flags[1].filters, [])

    def test_remove_flag(self):
        next_step = self.testWorkflow.steps["start"].conditionals[0]
        self.assertEqual(len(next_step.flags), 1)
        success = next_step.remove_flag(index=0)
        self.assertTrue(success)
        self.assertEqual(len(next_step.flags), 0)

        # Tests the XML representation after changes
        xml = self.testWorkflow.to_xml()
        step = xml.findall(".//steps/step/[@id='start']/next")

        next_step_flags_xml = xml.findall(".//steps/step/[@id='start']/next")
        self.assertEqual(len(next_step_flags_xml), 1)

    def test_update_flag(self):
        self.assertEqual(self.testWorkflow.steps["start"].conditionals[0].flags[0].action, "regMatch")
        self.testWorkflow.steps["start"].conditionals[0].flags[0].set(attribute="action", value="count")
        self.assertEqual(self.testWorkflow.steps["start"].conditionals[0].flags[0].action, "count")

        # Check the XML output
        xml = self.testWorkflow.to_xml()
        self.assertEqual(xml.find(".//steps/step/[@id='start']/next/[@step='1']/flag[1]").get("action"), "count")

    def test_display_flag(self):
        output = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].flags[0].__repr__())
        self.assertTrue(output["action"])
        self.assertTrue(output["args"])

    """
        CRUD - Filter
    """

    def test_create_filter(self):
        conditional = self.testWorkflow.steps["start"].conditionals[0].flags[0]
        self.assertEqual(len(conditional.filters), 1)

        conditional.add_filter(action="length", args={"test": "test"})
        self.assertEqual(len(conditional.filters), 2)
        self.assertEqual(conditional.filters[1].action, "length")
        self.assertTrue(conditional.filters[1].args["test"])

        # Tests adding a filter at index
        conditional.add_filter(action="length", args={"test2": "test2"}, index=1)
        self.assertEqual(len(conditional.filters), 3)
        self.assertEqual(conditional.filters[1].action, "length")
        self.assertTrue(conditional.filters[1].args["test2"])
        self.assertEqual(conditional.filters[2].action, "length")
        self.assertTrue(conditional.filters[2].args["test"])

        xml = self.testWorkflow.to_xml()

        # Check XML
        self.assertEqual(len(
            xml.findall(".//steps/step/[@id='start']/next/[@step='1']/flag/[@action='regMatch']/filters/filter")), 3)
        self.assertEqual(len(xml.findall(
            ".//steps/step/[@id='start']/next/[@step='1']/flag/[@action='regMatch']/filters/filter[2]/args/test2")), 1)
        self.assertEqual(len(xml.findall(
            ".//steps/step/[@id='start']/next/[@step='1']/flag/[@action='regMatch']/filters/filter[3]/args/test")), 1)

    def test_remove_filter(self):
        conditional = self.testWorkflow.steps["start"].conditionals[0].flags[0]
        conditional.add_filter(action="length", args={"test": "test"})
        conditional.add_filter(action="length", args={"test2": "test2"}, index=1)
        self.assertEqual(len(conditional.filters), 3)

        conditional.remove_filter(index=0)
        self.assertEqual(len(conditional.filters), 2)
        self.assertEqual(conditional.filters[1].action, "length")
        self.assertTrue(conditional.filters[1].args["test"])
        self.assertEqual(conditional.filters[0].action, "length")
        self.assertTrue(conditional.filters[0].args["test2"])

        xml = self.testWorkflow.to_xml()

        # Check XML
        self.assertEqual(len(
            xml.findall(".//steps/step/[@id='start']/next/[@step='1']/flag/[@action='regMatch']/filters/filter")), 2)
        self.assertEqual(len(xml.findall(
            ".//steps/step/[@id='start']/next/[@step='1']/flag/[@action='regMatch']/filters/filter[1]/args/test2")), 1)
        self.assertEqual(len(xml.findall(
            ".//steps/step/[@id='start']/next/[@step='1']/flag/[@action='regMatch']/filters/filter[2]/args/test")), 1)

    def test_update_filter(self):
        conditional = self.testWorkflow.steps["start"].conditionals[0].flags[0]
        self.assertEqual(conditional.filters[0].action, "length")
        conditional.filters[0].action = "combine"
        self.assertEqual(conditional.filters[0].action, "combine")

        xml = self.testWorkflow.to_xml()
        # Check XML
        self.assertEqual(
            xml.find(".//steps/step/[@id='start']/next/[@step='1']/flag/[@action='regMatch']/filters/filter[1]").get(
                "action"), "combine")

    def test_display_filter(self):
        conditional = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].flags[0].filters.__repr__())
        self.assertEqual(len(conditional), 1)
        self.assertEqual(conditional[0]["action"], "length")

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
        stepOne = Step(name="test_step_one", ancestry=workflow.ancestry)
        stepTwo = Step(name="test_step_two", ancestry=workflow.ancestry)
        workflow.steps["test_step_one"] = stepOne
        workflow.steps["test_step_two"] = stepTwo

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

        workflow.create_step(name="stepOne", app='HelloWorld', action='invalid_name', risk=1)
        workflow.steps["stepOne"].inputs = {'call': Argument(key='call', value='HelloWorld', format='str')}
        workflow.create_step(name="stepTwo", app='HelloWorld', action='repeatBackToMe', risk=2)
        workflow.steps["stepTwo"].inputs = {'number': Argument(key='number', value='6', format='str')}
        workflow.create_step(name="stepThree", app='HelloWorld', action='returnPlusOne', risk=3)
        workflow.steps["stepThree"].inputs = {}

        instance = Instance.create(app_name='HelloWorld', device_name='test_device_name')

        workflow._Workflow__execute_step(workflow.steps["stepOne"], instance=instance())
        self.assertEqual(workflow.accumulated_risk, 1.0/6.0)
        workflow._Workflow__execute_step(workflow.steps["stepTwo"], instance=instance())
        self.assertEqual(workflow.accumulated_risk, (1.0/6.0)+(2.0/6.0))
        workflow._Workflow__execute_step(workflow.steps["stepThree"], instance=instance())
        self.assertEqual(workflow.accumulated_risk, 1.0)
