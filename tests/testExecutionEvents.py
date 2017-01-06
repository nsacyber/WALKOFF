import unittest
from core import controller, case

class TestExecutionEvents(unittest.TestCase):

    def test_executionEvents(self):
        c = controller.Controller(name="testExecutionEventsController")
        c.loadWorkflowsFromFile(path="tests/testWorkflows/multiactionWorkflowTest.workflow")

        executionCase = case.Case(subscriptions={"testExecutionEventsController": ["instanceCreated", "stepExecutedSuccessfully", "nextStepFound", "workflowShutdown"]}, history=[])

        case.addCase(name="testExecutionEvents", case=executionCase)

        history = case.cases["testExecutionEvents"]
        with history:
            c.executeWorkflow(name="multiactionWorkflow")
            self.assertTrue(len(history.history) == 6)











