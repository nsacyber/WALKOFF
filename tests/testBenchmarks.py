import unittest
from core import graphDecorator, controller, case

class TestExecutionLoads(unittest.TestCase):
    """
        Benchmarks 1000 simple execution events at once
    """

    @graphDecorator.callgraph(enabled=True)
    def test_ffkExecutionEvents(self):
        c = controller.Controller(name="benchmark1000Controller")
        c.loadWorkflowsFromFile(path="tests/testWorkflows/basicWorkflowTest.workflow")

        executionCase = case.Case(subscriptions={
            "helloWorldWorkflow:start": ["functionExecutedSuccessfully", "inputValidated", "conditionalsExecuted"]},
            history=[])

        case.addCase(name="benchmark1000Events", case=executionCase)

        history = case.cases["benchmark1000Events"]

        for x in range(0, 1000):
            c.executeWorkflow(name="helloWorldWorkflow")

