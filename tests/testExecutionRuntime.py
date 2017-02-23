import ast
import unittest
from os import mkdir
from os.path import isdir

from core import config as core_config
from core import controller
from core import graphDecorator
from tests import config


class TestExecutionRuntime(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        if not isdir(core_config.profileVisualizationsPath):
            mkdir(core_config.profileVisualizationsPath)

    """
        Tests the out templating function which replaces the value of an argument with the output from the workflow history.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_TemplatedWorkflow(self):
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "templatedWorkflowTest.workflow")
        steps, instances = self.c.executeWorkflow("templatedWorkflow")
        instances = ast.literal_eval(instances)
        self.assertEqual(len(steps), 2, 'Unexpected number of steps executed. '
                                        'Expected {0}, got {1}'.format(2, len(steps)))
        self.assertEqual(steps[0].name, "start")
        self.assertDictEqual(steps[0].output, {"message": "HELLO WORLD"})
        self.assertEqual(steps[0].nextUp, "1")
        self.assertEqual(steps[1].name, "1")
        self.assertEqual(steps[1].output, "REPEATING: {'message': 'HELLO WORLD'}")
        self.assertIsNone(steps[1].nextUp)
        self.assertEqual(instances["hwTest"]["state"], '0')

    """
        Tests the calling of nested workflows
    """

    @graphDecorator.callgraph(enabled=False)
    def test_SimpleTieredWorkflow(self):
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "tieredWorkflow.workflow")
        steps, instances = self.c.executeWorkflow("parentWorkflow")
        output = [step.output for step in steps]
        self.assertEqual(output[0], "REPEATING: Parent Step One")
        self.assertEqual(output[1], "REPEATING: Child Step One")
        self.assertEqual(output[2], "REPEATING: Parent Step Two")

    """
        Tests a workflow that loops a few times
    """

    @graphDecorator.callgraph(enabled=False)
    def test_Loop(self):
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/loopWorkflow.workflow")
        steps, instances = self.c.executeWorkflow("loopWorkflow")
        output = [step.output for step in steps]
        self.assertEqual(len(output), 5)
