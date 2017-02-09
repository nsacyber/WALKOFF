import unittest, ast
from core import controller, case
from core import graphDecorator
from core import config as coreConfig
from os.path import isdir
from os import mkdir
from tests import config
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED


class TestExecutionRuntime(unittest.TestCase):
    def setUp(self):
        self.c = controller.Controller()
        if not isdir(coreConfig.profileVisualizationsPath):
            mkdir(coreConfig.profileVisualizationsPath)

    """
        Tests the out templating function which replaces the value of an argument with the output from the workflow history.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_TemplatedWorkflow(self):
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "templatedWorkflowTest.workflow")
        steps, instances = self.c.executeWorkflow("templatedWorkflow")
        instances = ast.literal_eval(instances)
        self.assertTrue(len(steps) == 2)
        self.assertTrue(steps[0].name == "start")
        self.assertTrue(steps[0].output == {"message": "HELLO WORLD"})
        self.assertTrue(steps[0].nextUp == "1")
        self.assertTrue(steps[1].name == "1")
        self.assertTrue(steps[1].output == "REPEATING: {'message': 'HELLO WORLD'}")
        self.assertTrue(steps[1].nextUp == None)
        self.assertTrue(instances["hwTest"]["state"] == '0')

    """
        Tests the calling of nested workflows
    """

    @graphDecorator.callgraph(enabled=False)
    def test_SimpleTieredWorkflow(self):
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "tieredWorkflow.workflow")
        steps, instances = self.c.executeWorkflow("parentWorkflow")
        output = [step.output for step in steps]
        self.assertTrue(output[0] == "REPEATING: Parent Step One")
        self.assertTrue(output[1] == "REPEATING: Child Step One")
        self.assertTrue(output[2] == "REPEATING: Parent Step Two")

    """
        Tests a workflow that loops a few times
    """

    @graphDecorator.callgraph(enabled=True)
    def test_Loop(self):
        history = case.Case(subscriptions=[{
            "object": self.c,
            "events": [EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED,
                       EVENT_SCHEDULER_RESUMED,
                       EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                       EVENT_JOB_EXECUTED, EVENT_JOB_ERROR]
        }])
        self.c.loadWorkflowsFromFile(path="tests/testWorkflows/loopWorkflow.workflow")
        steps, instances = self.c.executeWorkflow("loopWorkflow")
        output = [step.output for step in steps]
        self.assertTrue(len(output) == 5)
