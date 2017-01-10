import unittest
from core import controller, case, graphDecorator

class TestExecutionEvents(unittest.TestCase):

    @graphDecorator.callgraph(enabled=False)
    def test_workflowExecutionEvents(self):
        c = controller.Controller(name="testExecutionEventsController")
        c.loadWorkflowsFromFile(path="tests/testWorkflows/multiactionWorkflowTest.workflow")

        executionCase = case.Case(subscriptions={"testExecutionEventsController": ["instanceCreated", "stepExecutedSuccessfully", "nextStepFound", "workflowShutdown"]}, history=[])

        case.addCase(name="testExecutionEvents", case=executionCase)

        history = case.cases["testExecutionEvents"]
        with history:
            c.executeWorkflow(name="multiactionWorkflow")
            self.assertTrue(len(history.history) == 6)

    @graphDecorator.callgraph(enabled=False)
    def test_stepExecutionEvents(self):
        c = controller.Controller(name="testStepExecutionEventsController")
        c.loadWorkflowsFromFile(path="tests/testWorkflows/basicWorkflowTest.workflow")

        executionCase = case.Case(subscriptions={"helloWorldWorkflow:start": ["functionExecutedSuccessfully", "inputValidated", "conditionalsExecuted"]}, history=[])

        case.addCase(name="testStepExecutionEvents", case=executionCase)

        history = case.cases["testStepExecutionEvents"]
        with history:
            c.executeWorkflow(name="helloWorldWorkflow")
            print(len(history.history))
            self.assertTrue(len(history.history) == 3)













