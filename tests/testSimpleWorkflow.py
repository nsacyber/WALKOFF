import unittest

from core import controller, graphDecorator
from tests import config
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import *
from server import flaskServer as server


class TestSimpleWorkflow(unittest.TestCase):
    def setUp(self):
        case_database.initialize()
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        self.c = controller.Controller()
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "basicWorkflowTest.workflow")
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "multiactionWorkflowTest.workflow")
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "multistepError.workflow")
        self.start = datetime.utcnow()

    def tearDown(self):
        case_database.case_db.tearDown()
        case_subscription.clear_subscriptions()

    """
        Tests simple workflow execution with a single action with an argument and no jumps.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_SimpleWorkflowExecution(self):
        setup_subscriptions_for_step('helloWorldWorkflow', ['start'])
        self.c.executeWorkflow('helloWorldWorkflow')
        steps = executed_steps('defaultController', 'helloWorldWorkflow', self.start, datetime.utcnow())
        self.assertEqual(len(steps), 1)
        step = steps[0]
        ancestry = step['ancestry'].split(',')
        self.assertEqual(ancestry[-1], "start")
        self.assertEqual(step['data']['result'], "REPEATING: Hello World")

    """
        Tests workflow execution that has multiple steps.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_MultiActionWorkflow(self):
        workflow_name = 'multiactionWorkflow'
        step_names = ['start', '1']
        setup_subscriptions_for_step(workflow_name, step_names)
        self.c.executeWorkflow(workflow_name)
        steps = executed_steps('defaultController', workflow_name, self.start, datetime.utcnow())
        self.assertEqual(len(steps), 2)
        names = [step['ancestry'].split(',')[-1] for step in steps]
        orderless_list_compare(self, names, step_names)
        name_result = {'start': {"message": "HELLO WORLD"},
                       '1': "REPEATING: Hello World"}
        for step in steps:
            name = step['ancestry'].split(',')[-1]
            self.assertIn(name, name_result)
            if type(name_result[name]) == dict:
                self.assertDictEqual(step['data']['result'], name_result[name])
            else:
                self.assertEqual(step['data']['result'], name_result[name])

    """
            Tests workflow execution that has an error in the second step. Then moves to step "error" instead.
    """

    def test_ErrorWorkflow(self):
        workflow_name = 'multiactionErrorWorkflow'
        step_names = ['start', '1', 'error']
        setup_subscriptions_for_step(workflow_name, step_names)
        self.c.executeWorkflow(workflow_name)
        steps = executed_steps('defaultController', workflow_name, self.start, datetime.utcnow())
        self.assertEqual(len(steps), 2)
        names = [step['ancestry'].split(',')[-1] for step in steps]
        orderless_list_compare(self, names, ['start', 'error'])
        name_result = {'start': {"message": "HELLO WORLD"},
                       'error': "REPEATING: Hello World"}
        for step in steps:
            name = step['ancestry'].split(',')[-1]
            self.assertIn(name, name_result)
            if type(name_result[name]) == dict:
                self.assertDictEqual(step['data']['result'], name_result[name])
            else:
                self.assertEqual(step['data']['result'], name_result[name])
