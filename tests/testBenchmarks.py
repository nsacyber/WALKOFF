import unittest
from os import mkdir
from os.path import isdir

from core import config as core_config
from core import graphDecorator, controller, case
from tests import config


class TestExecutionLoads(unittest.TestCase):
    """
        Benchmarks 1000 simple execution events at once
    """

    def setUp(self):
        if not isdir(core_config.profileVisualizationsPath):
            mkdir(core_config.profileVisualizationsPath)

    @graphDecorator.callgraph(enabled=True)
    def test_ffkExecutionEvents(self):
        c = controller.Controller(name="benchmark1000Controller")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + 'basicWorkflowTest.workflow')

        executionCase = case.subscription.CaseSubscriptions(subscriptions={
            "helloWorldWorkflow:start": ["FunctionExecutedSuccessfully", "InputValidated", "ConditionalsExecuted"]},
            history=[])

        case.addCase(name="benchmark1000Events", case=executionCase)

        history = case.cases["benchmark1000Events"]

        for x in range(0, 1000):
            c.executeWorkflow(name="helloWorldWorkflow")
