import unittest, ast
from core import controller

class TestSimpleWorkflow(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/basicWorkflowTest.workflow")
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/multiactionWorkflowTest.workflow")
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/templatedWorkflowTest.workflow")

    """
        Tests simple workflow execution with a single action with an argument and no jumps.
    """
    def test_SimpleWorkflowExecution(self):
        steps, instances = self.c.workflows["helloWorldWorkflow"].execute()
        instances = ast.literal_eval(instances)
        self.assertTrue(len(steps) == 1)
        self.assertTrue(steps[0].id == "start")
        self.assertTrue(steps[0].output == "REPEATING: Hello World")
        print(steps[0].nextUp)
#        self.assertTrue(steps[0].nextUp == None)
        self.assertTrue(instances["hwTest"]["state"] == '0')


    """
        Tests workflow execution that has multiple steps.
    """
    def test_MultiActionWorkflow(self):
        steps, instances = self.c.workflows["multiactionWorkflow"].execute()
        instances = ast.literal_eval(instances)
        self.assertTrue(len(steps) == 2)
        self.assertTrue(steps[0].id == "start")
        self.assertTrue(steps[0].output == {"message":"HELLO WORLD"})
        self.assertTrue(steps[0].nextUp == "1")
        self.assertTrue(steps[1].id == "1")
        self.assertTrue(steps[1].output == "REPEATING: Hello World")
        self.assertTrue(steps[1].nextUp == None)
        self.assertTrue(instances["hwTest"]["state"] == '0')




