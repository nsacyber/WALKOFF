import unittest
from core import controller, case, graphDecorator
from tests import config


class TestExecutionEvents(unittest.TestCase):
    """
            Tests execution Events at the Workflow Level
    """
    def setUp(self):
        case.cases = {}


    @graphDecorator.callgraph(enabled=False)
    def test_workflowExecutionEvents(self):
        c = controller.Controller(name="testExecutionEventsController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "multiactionWorkflowTest.workflow")

        executionCase = case.Case(subscriptions={
            "testExecutionEventsController": ["InstanceCreated", "StepExecutionSuccess", "NextStepFound",
                                              "WorkflowShutdown"]}, history=[])

        case.addCase(name="testExecutionEvents", case=executionCase)
        history = case.cases["testExecutionEvents"]
        with history:
            c.executeWorkflow(name="multiactionWorkflow")
            self.assertTrue(len(history.history) == 6)

    """
        Tests execution events at the Step Level
    """

    @graphDecorator.callgraph(enabled=False)
    def test_stepExecutionEvents(self):
        c = controller.Controller(name="testStepExecutionEventsController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "basicWorkflowTest.workflow")

        executionCase = case.Case(subscriptions={
            "helloWorldWorkflow:start": ["FunctionExecutionSuccess", "InputValidated", "ConditionalsExecuted"]},
            history=[])

        case.addCase(name="testStepExecutionEvents", case=executionCase)

        history = case.cases["testStepExecutionEvents"]
        with history:
            c.executeWorkflow(name="helloWorldWorkflow")
            self.assertTrue(len(history.history) == 3)

    """
        Tests execution events at the Filter Flag and Keyword Level
    """

    @graphDecorator.callgraph(enabled=False)
    def test_ffkExecutionEvents(self):
        c = controller.Controller(name="testStepFFKEventsController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "basicWorkflowTest.workflow")

        executionCase = case.Case(subscriptions={
            "helloWorldWorkflow:start": ["FunctionExecutionSuccess", "InputValidated", "ConditionalsExecuted",
                                         'NextStepTaken', 'NextStepNotTaken',
                                         'FlagArgsValid', 'FlagArgsInvalid',
                                         'FilterSuccess', 'FilterError']},
            history=[])

        case.addCase(name="testStepFFKEventsEvents", case=executionCase)

        history = case.cases["testStepFFKEventsEvents"]
        with history:
            c.executeWorkflow(name="helloWorldWorkflow")
            self.assertTrue(len(history.history) == 6)
