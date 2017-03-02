import unittest
from os import mkdir
from os.path import isdir

from core import config as core_config
from core import graphDecorator, controller
from core.case.subscription import CaseSubscriptions, Subscription, set_subscriptions
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

        step_subs = Subscription(events=['FunctionExecutedSuccessfully',
                                         'InputValidated',
                                         'ConditionalsExecuted'])
        case_sub = {'benchmark1000Controller': Subscription(subscriptions={
                'hellWorldWorkflow': Subscription(subscriptions={'start': step_subs})})}

        execution_case = CaseSubscriptions(subscriptions=case_sub)
        set_subscriptions({'case1': execution_case})

        for x in range(1000):
            c.executeWorkflow(name="helloWorldWorkflow")
