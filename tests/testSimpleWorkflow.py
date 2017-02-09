import unittest, ast
from core import controller, graphDecorator
from tests import config


class TestSimpleWorkflow(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "basicWorkflowTest.workflow")
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "multiactionWorkflowTest.workflow")
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "templatedWorkflowTest.workflow")
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "multistepError.workflow")

    """
        Tests simple workflow execution with a single action with an argument and no jumps.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_SimpleWorkflowExecution(self):
        steps, instances = self.c.executeWorkflow("helloWorldWorkflow")
        instances = ast.literal_eval(instances)
        self.assertTrue(len(steps) == 1)
        self.assertTrue(steps[0].name == "start")
        self.assertTrue(steps[0].output == "REPEATING: Hello World")
        # self.assertTrue(steps[0].nextUp == None)
        self.assertTrue(instances["hwTest"]["state"] == '0')

    """
        Tests workflow execution that has multiple steps.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_MultiActionWorkflow(self):
        steps, instances = self.c.executeWorkflow("multiactionWorkflow")
        instances = ast.literal_eval(instances)
        self.assertTrue(len(steps) == 2)
        self.assertTrue(steps[0].name == "start")
        self.assertTrue(steps[0].output == {"message": "HELLO WORLD"})
        self.assertTrue(steps[0].nextUp == "1")
        self.assertTrue(steps[1].name == "1")
        self.assertTrue(steps[1].output == "REPEATING: Hello World")
        self.assertTrue(steps[1].nextUp == None)
        self.assertTrue(instances["hwTest"]["state"] == '0')

    """
            Tests workflow execution that has an error in the second step. Then moves to step "error" instead.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_ErrorWorkflow(self):
        steps, instances = self.c.executeWorkflow("multiactionErrorWorkflow")
        instances = ast.literal_eval(instances)
        self.assertTrue(len(steps) == 3)
        self.assertTrue(steps[0].name == "start")
        self.assertTrue(steps[0].output == {"message": "HELLO WORLD"})
        self.assertTrue(steps[0].nextUp == "1")
        self.assertTrue(steps[1].nextUp == "error")
        self.assertTrue(steps[2].name == "error")
        self.assertTrue(steps[2].output == "REPEATING: Hello World")
        self.assertTrue(instances["hwTest"]["state"] == '0')
