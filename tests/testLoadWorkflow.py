import unittest, os
from core import controller
from core import arguments



class TestLoadWorkflow(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/basicWorkflowTest.workflow")
        self.testWorkflow = self.c.workflows["helloWorldWorkflow"]

    def test_workflowLoaded(self):
        #Tests that helloWorldWorkflow exists
        self.assertTrue("helloWorldWorkflow" in self.c.workflows)

    def test_workflowOptions(self):
        self.assertTrue(self.testWorkflow.options == [{'enabled': 'true'}, {'scheduler': {'sDT': '2016-1-1 12:00:00', 'eDT': '2016-3-15 12:00:00', 'interval': '0.1', 'autorun': 'true'}}])

    def test_baseWorkflowAttributes(self):
        #Correct number of steps
        self.assertTrue(len(self.testWorkflow.steps) == 1)

        #Asserts workflow entry point
        self.assertTrue(self.testWorkflow.steps["start"])
        step = self.testWorkflow.steps["start"]

        #Verify attributes
        self.assertTrue(step.id == "start")
        self.assertTrue(step.app == "HelloWorld")
        self.assertTrue(step.action == "repeatBackToMe")
        self.assertTrue(step.device == "hwTest")

    def test_workflowInput(self):
        arg = arguments.Argument(key="call", value="Hello World", type="string")
        # self.assertTrue(step.input == {"call":arg})

    def test_workflowNextSteps(self):
        next = self.testWorkflow.steps["start"].conditionals
        self.assertTrue(len(next) == 1)

        next = next[0]
        self.assertTrue(next.nextStep == "1")
        self.assertTrue(next.flags)


    def test_workflowNextStepFlags(self):
        flags = self.testWorkflow.steps["start"].conditionals[0].flags

        # Verify flags exist
        self.assertTrue(len(flags) == 1)

        flag = flags[0]
        self.assertTrue(flag.action == "regMatch")
        #self.assertDictEqual({'regex': {'key': 'regex', 'type': 'regex', 'value': '(.*)'}}, flag.args)
        self.assertTrue(flag.filters)

    def test_workflowNextStepFilters(self):
        filters = self.testWorkflow.steps["start"].conditionals[0].flags[0].filters
        self.assertTrue(len(filters) == 1)

        filter = filters[0]
        self.assertTrue(filter.action == "length")
        self.assertTrue(filter.args == {})

    def test_workflowError(self):
        errors = self.testWorkflow.steps["start"].errors
        self.assertTrue(len(errors) == 1)
        self.assertTrue(errors[0].nextStep == "1")



