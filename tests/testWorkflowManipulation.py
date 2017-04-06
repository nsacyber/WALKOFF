import ast
import unittest
from datetime import datetime
from os import path
from core import controller, graphDecorator
import core.case.database as case_database
import core.case.subscription as case_subscription
from core.helpers import construct_workflow_name_key
from tests import config
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
from core.controller import _WorkflowKey
from server import flaskServer as flask_server
from server.flaskServer import running_context


class TestWorkflowManipulation(unittest.TestCase):
    def setUp(self):
        case_database.initialize()
        self.app = flask_server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        self.c = controller.Controller(appPath=path.join(".", "tests", "testWorkflows", "testGeneratedWorkflows"))
        self.c.loadWorkflowsFromFile(
            path=path.join(config.test_workflows_path, 'simpleDataManipulationWorkflow.workflow'))
        self.id_tuple = ('simpleDataManipulationWorkflow', 'helloWorldWorkflow')
        self.workflow_name = construct_workflow_name_key(*self.id_tuple)
        self.testWorkflow = self.c.get_workflow(*self.id_tuple)

    def tearDown(self):
        self.c.workflows = None
        case_database.case_db.tearDown()
        case_subscription.clear_subscriptions()

    def executionTest(self):
        running_context.init_threads()
        step_names = ['start', '1']
        setup_subscriptions_for_step(self.testWorkflow.name, step_names)
        start = datetime.utcnow()
        # Check that the workflow executed correctly post-manipulation
        self.c.executeWorkflow(*self.id_tuple)

        running_context.shutdown_threads()

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

    @graphDecorator.callgraph(enabled=False)
    def test_createWorkflow(self):
        self.assertEqual(len(self.c.workflows), 2)
        # Create Empty Workflow
        self.c.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.assertEqual(len(self.c.workflows), 3)
        workflow_name = construct_workflow_name_key('emptyWorkflow', 'emptyWorkflow')
        self.assertEqual(self.c.get_workflow('emptyWorkflow', 'emptyWorkflow').steps, {})

        xml = self.c.get_workflow('emptyWorkflow', 'emptyWorkflow').to_xml()
        self.assertEqual(len(xml.findall(".//steps/*")), 0)

    @graphDecorator.callgraph(enabled=False)
    def test_removeWorkflow(self):
        initial_workflows = list(self.c.workflows.keys())
        self.c.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.assertEqual(len(self.c.workflows), 3)
        success = self.c.removeWorkflow('emptyWorkflow', 'emptyWorkflow')
        self.assertTrue(success)
        self.assertEqual(len(self.c.workflows), 2)
        key = _WorkflowKey('emptyWorkflow', 'emptyWorkflow')
        self.assertNotIn(key, self.c.workflows)
        orderless_list_compare(self, list(self.c.workflows.keys()), initial_workflows)

    @graphDecorator.callgraph(enabled=False)
    def test_updateWorkflow(self):
        self.c.create_workflow_from_template('emptyWorkflow', 'emptyWorkflow')
        self.c.update_workflow_name('emptyWorkflow', 'emptyWorkflow', 'newPlaybookName', 'newWorkflowName')
        old_key = _WorkflowKey('emptyWorkflow', 'emptyWorkflow')
        new_key = _WorkflowKey('newPlaybookName', 'newWorkflowName')
        self.assertEqual(len(self.c.workflows), 3)
        self.assertNotIn(old_key, self.c.workflows)
        self.assertIn(new_key, self.c.workflows)

    @graphDecorator.callgraph(enabled=False)
    def test_displayWorkflow(self):
        workflow = ast.literal_eval(self.testWorkflow.__repr__())
        self.assertEqual(len(workflow["steps"]), 1)
        self.assertTrue(workflow["options"])

    """
        CRUD - Step
    """

    @graphDecorator.callgraph(enabled=False)
    def test_createStep(self):
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

        self.executionTest()

    @graphDecorator.callgraph(enabled=False)
    def test_addStepToXML(self):
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

        self.executionTest()

    @graphDecorator.callgraph(enabled=False)
    def test_removeStep(self):
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

    @graphDecorator.callgraph(enabled=False)
    def test_updateStep(self):
        self.assertEqual(self.testWorkflow.steps["start"].action, "repeatBackToMe")
        self.testWorkflow.steps["start"].action = "helloWorld"
        self.assertEqual(self.testWorkflow.steps["start"].action, "helloWorld")

        xml = self.testWorkflow.to_xml()
        self.assertEqual(xml.find(".//steps/step/[@id='start']/action").text, "helloWorld")

    @graphDecorator.callgraph(enabled=False)
    def test_displaySteps(self):
        output = ast.literal_eval(self.testWorkflow.__repr__())
        self.assertTrue(output["options"])
        self.assertTrue(output["steps"])
        self.assertEqual(len(output["steps"]), 1)
        self.assertEqual(output["steps"]["start"]["action"], "repeatBackToMe")

    """
        CRUD - Next
    """

    @graphDecorator.callgraph(enabled=False)
    def test_updateNext(self):
        step = self.testWorkflow.steps["start"]
        self.assertEqual(step.conditionals[0].name, "1")
        step.conditionals[0].name = "2"
        self.assertEqual(step.conditionals[0].name, "2")

        xml = self.testWorkflow.to_xml()

        # Check XML
        self.assertEqual(xml.find(".//steps/step/[@id='start']/next").get("step"), "2")

    @graphDecorator.callgraph(enabled=False)
    def test_displayNext(self):
        conditional = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].__repr__())
        self.assertTrue(conditional["flags"])
        self.assertEqual(conditional["name"], "1")

    """
        CRUD - Flag
    """

    @graphDecorator.callgraph(enabled=False)
    def test_createFlag(self):
        nextStep = self.testWorkflow.steps["start"].conditionals[0]
        self.assertEqual(len(nextStep.flags), 1)
        nextStep.create_flag(action="count", args={"operator": "ge", "threshold": "1"}, filters=[])
        self.assertEqual(len(nextStep.flags), 2)
        self.assertEqual(nextStep.flags[1].action, "count")
        self.assertDictEqual(nextStep.flags[1].args, {"operator": "ge", "threshold": "1"})
        self.assertEqual(nextStep.flags[1].filters, [])

    @graphDecorator.callgraph(enabled=False)
    def test_removeFlag(self):
        nextStep = self.testWorkflow.steps["start"].conditionals[0]
        self.assertEqual(len(nextStep.flags), 1)
        success = nextStep.remove_flag(index=0)
        self.assertTrue(success)
        self.assertEqual(len(nextStep.flags), 0)

        # Tests the XML representation after changes
        xml = self.testWorkflow.to_xml()
        step = xml.findall(".//steps/step/[@id='start']/next")

        nextStepFlagsXML = xml.findall(".//steps/step/[@id='start']/next")
        self.assertEqual(len(nextStepFlagsXML), 1)

    @graphDecorator.callgraph(enabled=False)
    def test_updateFlag(self):
        self.assertEqual(self.testWorkflow.steps["start"].conditionals[0].flags[0].action, "regMatch")
        self.testWorkflow.steps["start"].conditionals[0].flags[0].set(attribute="action", value="count")
        self.assertEqual(self.testWorkflow.steps["start"].conditionals[0].flags[0].action, "count")

        # Check the XML output
        xml = self.testWorkflow.to_xml()
        self.assertEqual(xml.find(".//steps/step/[@id='start']/next/[@step='1']/flag[1]").get("action"), "count")

    @graphDecorator.callgraph(enabled=False)
    def test_displayFlag(self):
        output = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].flags[0].__repr__())
        self.assertTrue(output["action"])
        self.assertTrue(output["args"])

    """
        CRUD - Filter
    """

    @graphDecorator.callgraph(enabled=False)
    def test_createFilter(self):
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

    @graphDecorator.callgraph(enabled=False)
    def test_removeFilter(self):
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

    @graphDecorator.callgraph(enabled=False)
    def test_updateFilter(self):
        conditional = self.testWorkflow.steps["start"].conditionals[0].flags[0]
        self.assertEqual(conditional.filters[0].action, "length")
        conditional.filters[0].action = "combine"
        self.assertEqual(conditional.filters[0].action, "combine")

        xml = self.testWorkflow.to_xml()
        # Check XML
        self.assertEqual(
            xml.find(".//steps/step/[@id='start']/next/[@step='1']/flag/[@action='regMatch']/filters/filter[1]").get(
                "action"), "combine")

    @graphDecorator.callgraph(enabled=False)
    def test_displayFilter(self):
        conditional = ast.literal_eval(self.testWorkflow.steps["start"].conditionals[0].flags[0].filters.__repr__())
        self.assertEqual(len(conditional), 1)
        self.assertEqual(conditional[0]["action"], "length")

    def test_to_from_cytoscape_data(self):
        self.c.loadWorkflowsFromFile(path=path.join(config.test_workflows_path, 'multiactionWorkflowTest.workflow'))
        workflow = self.c.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        original_steps = {step_name: step.as_json() for step_name, step in workflow.steps.items()}
        cytoscape_data = workflow.get_cytoscape_data()
        workflow.steps = {}
        workflow.from_cytoscape_data(cytoscape_data)
        derived_steps = {step_name: step.as_json() for step_name, step in workflow.steps.items()}
        self.assertDictEqual(derived_steps, original_steps)

    """
        CRUD - Options
    """

    @graphDecorator.callgraph(enabled=False)
    def test_createOption(self):
        self.assertEqual(True, True)

    @graphDecorator.callgraph(enabled=False)
    def test_removeOption(self):
        self.assertEqual(True, True)

    @graphDecorator.callgraph(enabled=False)
    def test_updateOption(self):
        self.assertEqual(True, True)

    @graphDecorator.callgraph(enabled=False)
    def test_displayOption(self):
        self.assertEqual(True, True)
