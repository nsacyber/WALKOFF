import unittest, ast

from core import controller

class TestExecutionRuntime(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()

    """
            Tests the out templating function which replaces the value of an argument with the output from the workflow history.
    """
    def test_TemplatedWorkflow(self):
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/templatedWorkflowTest.workflow")
        steps, instances = self.c.executeWorkflow("templatedWorkflow")
        instances = ast.literal_eval(instances)
        self.assertTrue(len(steps) == 2)
        self.assertTrue(steps[0].id == "start")
        self.assertTrue(steps[0].output == {"message": "HELLO WORLD"})
        self.assertTrue(steps[0].nextUp == "1")
        self.assertTrue(steps[1].id == "1")
        self.assertTrue(steps[1].output == "REPEATING: {'message': 'HELLO WORLD'}")
        self.assertTrue(steps[1].nextUp == None)
        self.assertTrue(instances["hwTest"]["state"] == '0')

    def test_SimpleTieredWorkflow(self):
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/tieredWorkflow.workflow")
        steps, instances = self.c.executeWorkflow("parentWorkflow")
        output = [step.output for step in steps]
        self.assertTrue(output[0] == "REPEATING: Parent Step One")
        self.assertTrue(output[1] == "REPEATING: Child Step One")
        self.assertTrue(output[2] == "REPEATING: Parent Step Two")

    def test_Loop(self):
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/loopWorkflow.workflow")
        steps, instances = self.c.executeWorkflow("loopWorkflow")
        output = [step.output for step in steps]
        self.assertTrue(len(output) == 5)





