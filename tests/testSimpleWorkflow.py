import ast
import unittest

from core import controller, graphDecorator
from tests import config
from server import flaskServer as server


class TestSimpleWorkflow(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
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
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].name, "start")
        self.assertEqual(steps[0].output, "REPEATING: Hello World")
        # self.assertTrue(steps[0].nextUp == None)
        self.assertEqual(instances["hwTest"]["state"], '0')

    """
        Tests workflow execution that has multiple steps.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_MultiActionWorkflow(self):
        steps, instances = self.c.executeWorkflow("multiactionWorkflow")
        instances = ast.literal_eval(instances)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].name, "start")
        self.assertDictEqual(steps[0].output, {"message": "HELLO WORLD"})
        self.assertEqual(steps[0].nextUp, "1")
        self.assertEqual(steps[1].name, "1")
        self.assertEqual(steps[1].output, "REPEATING: Hello World")
        self.assertIsNone(steps[1].nextUp)
        self.assertEqual(instances["hwTest"]["state"], '0')

    """
            Tests workflow execution that has an error in the second step. Then moves to step "error" instead.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_ErrorWorkflow(self):
        steps, instances = self.c.executeWorkflow("multiactionErrorWorkflow")
        instances = ast.literal_eval(instances)
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0].name, "start")
        self.assertDictEqual(steps[0].output, {"message": "HELLO WORLD"})
        self.assertEqual(steps[0].nextUp, "1")
        self.assertEqual(steps[1].nextUp, "error")
        self.assertEqual(steps[2].name, "error")
        self.assertEqual(steps[2].output, "REPEATING: Hello World")
        self.assertEqual(instances["hwTest"]["state"], '0')
