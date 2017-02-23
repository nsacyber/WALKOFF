import unittest

from core import arguments
from core import controller
from core import graphDecorator
from tests import config


class TestLoadWorkflow(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "basicWorkflowTest.workflow")
        self.testWorkflow = self.c.workflows["helloWorldWorkflow"]

    @graphDecorator.callgraph(enabled=False)
    def test_workflowLoaded(self):
        # Tests that helloWorldWorkflow exists
        self.assertTrue("helloWorldWorkflow" in self.c.workflows)

    @graphDecorator.callgraph(enabled=False)
    def test_baseWorkflowAttributes(self):
        # Correct number of steps
        self.assertEqual(len(self.testWorkflow.steps), 1)

        # Asserts workflow entry point
        self.assertTrue(self.testWorkflow.steps["start"])
        step = self.testWorkflow.steps["start"]

        # Verify attributes
        self.assertEqual(step.name, "start")
        self.assertEqual(step.app, "HelloWorld")
        self.assertEqual(step.action, "repeatBackToMe")
        self.assertEqual(step.device, "hwTest")

    @graphDecorator.callgraph(enabled=False)
    def test_workflowInput(self):
        arg = arguments.Argument(key="call", value="Hello World", format="string")
        # self.assertTrue(step.input == {"call":arg})

    @graphDecorator.callgraph(enabled=False)
    def test_workflowNextSteps(self):
        next = self.testWorkflow.steps["start"].conditionals
        self.assertEqual(len(next), 1)

        next = next[0]
        self.assertEqual(next.name, "1")
        self.assertTrue(next.flags)

    @graphDecorator.callgraph(enabled=False)
    def test_workflowNextStepFlags(self):
        flags = self.testWorkflow.steps["start"].conditionals[0].flags

        # Verify flags exist
        self.assertTrue(len(flags) == 1)

        flag = flags[0]
        self.assertEqual(flag.action, "regMatch")
        # self.assertDictEqual({'regex': {'key': 'regex', 'type': 'regex', 'value': '(.*)'}}, flag.args)
        self.assertTrue(flag.filters)

    @graphDecorator.callgraph(enabled=False)
    def test_workflowNextStepFilters(self):
        filters = self.testWorkflow.steps["start"].conditionals[0].flags[0].filters
        self.assertEqual(len(filters), 1)

        filter = filters[0]
        self.assertEqual(filter.action, "length")
        self.assertEqual(filter.args, {})

    @graphDecorator.callgraph(enabled=False)
    def test_workflowError(self):
        errors = self.testWorkflow.steps["start"].errors
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].name, "1")
