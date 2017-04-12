import unittest

from core import arguments
from core import controller
from core import graphdecorator
from tests import config
from core.controller import _WorkflowKey


class TestLoadWorkflow(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        self.c.load_workflows_from_file(path=config.test_workflows_path + 'basicWorkflowTest.workflow')
        self.workflow_name = _WorkflowKey('basicWorkflowTest', 'helloWorldWorkflow')
        self.testWorkflow = self.c.workflows[self.workflow_name]

    @graphdecorator.callgraph(enabled=False)
    def test_workflowLoaded(self):
        # Tests that helloWorldWorkflow exists
        self.assertIn(self.workflow_name, self.c.workflows)

    @graphdecorator.callgraph(enabled=False)
    def test_baseWorkflowAttributes(self):
        # Correct number of steps
        self.assertEqual(len(self.testWorkflow.steps), 1)

        # Asserts workflow entry point
        self.assertTrue(self.testWorkflow.steps['start'])
        step = self.testWorkflow.steps['start']

        # Verify attributes
        self.assertEqual(step.name, 'start')
        self.assertEqual(step.app, 'HelloWorld')
        self.assertEqual(step.action, 'repeatBackToMe')
        self.assertEqual(step.device, 'hwTest')

    @graphdecorator.callgraph(enabled=False)
    def test_workflowInput(self):
        arg = arguments.Argument(key='call', value='Hello World', format='string')
        #self.assertDictTrue(step.input == {"call":arg})

    @graphdecorator.callgraph(enabled=False)
    def test_workflowNextSteps(self):
        next_step = self.testWorkflow.steps['start'].conditionals
        self.assertEqual(len(next_step), 1)

        next_step = next_step[0]
        self.assertEqual(next_step.name, '1')
        self.assertTrue(next_step.flags)

    @graphdecorator.callgraph(enabled=False)
    def test_workflowNextStepFlags(self):
        flags = self.testWorkflow.steps['start'].conditionals[0].flags

        # Verify flags exist
        self.assertTrue(len(flags) == 1)

        flag = flags[0]
        self.assertEqual(flag.action, 'regMatch')
        # self.assertDictEqual({'regex': {'key': 'regex', 'type': 'regex', 'value': '(.*)'}}, flag.args)
        self.assertTrue(flag.filters)

    @graphdecorator.callgraph(enabled=False)
    def test_workflowNextStepFilters(self):
        filters = self.testWorkflow.steps['start'].conditionals[0].flags[0].filters
        self.assertEqual(len(filters), 1)

        filter_element = filters[0]
        self.assertEqual(filter_element.action, 'length')
        self.assertEqual(filter_element.args, {})

    @graphdecorator.callgraph(enabled=False)
    def test_workflowError(self):
        errors = self.testWorkflow.steps['start'].errors
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].name, '1')
