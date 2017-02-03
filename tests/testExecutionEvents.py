import unittest
from core import controller, case, graphDecorator
from tests import config
from core.case import Subscription


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
        subs = {'testExecutionEventsController':
                    Subscription(subscriptions=
                                 {'multiactionWorkflow':
                                      Subscription(events=["InstanceCreated", "StepExecutionSuccess",
                                                           "NextStepFound", "WorkflowShutdown"])})}
        executionCase = case.Case(subscriptions=subs, history=[])

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
        subs = {'testStepExecutionEventsController':
            Subscription(subscriptions=
            {'helloWorldWorkflow':
                Subscription(subscriptions=
                {'start':
                    Subscription(
                        events=["FunctionExecutionSuccess", "InputValidated",
                                "ConditionalsExecuted"])})})}
        executionCase = case.Case(subscriptions=subs, history=[])

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

        filter_sub = Subscription(events=['FilterSuccess', 'FilterError'])
        flag_sub = Subscription(events=['FlagArgsValid', 'FlagArgsInvalid'], subscriptions={'length': filter_sub})
        next_sub = Subscription(events=['NextStepTaken', 'NextStepNotTaken'], subscriptions={'regMatch': flag_sub})
        step_sub = Subscription(events=["FunctionExecutionSuccess", "InputValidated", "ConditionalsExecuted"],
                                subscriptions={'1': next_sub})
        subs = {'testStepFFKEventsController':
                    Subscription(subscriptions=
                                 {'helloWorldWorkflow':
                                      Subscription(subscriptions=
                                                   {'start': step_sub})})}
        executionCase = case.Case(subscriptions=subs, history=[])

        case.addCase(name="testStepFFKEventsEvents", case=executionCase)

        history = case.cases["testStepFFKEventsEvents"]
        with history:
            c.executeWorkflow(name="helloWorldWorkflow")
            self.assertTrue(len(history.history) == 6)

    @graphDecorator.callgraph(enabled=False)
    def test_ffkExecutionEventsCase(self):
        c = controller.Controller(name="testStepFFKEventsController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "basicWorkflowTest.workflow")
        filter_sub = Subscription(disabled=['FilterSuccess'])
        flag_sub = Subscription(subscriptions={'length': filter_sub})
        next_sub = Subscription(subscriptions={'regMatch': flag_sub})
        step_sub = Subscription(subscriptions={'1': next_sub})
        subs = {'testStepFFKEventsController':
                    Subscription(subscriptions=
                                 {'helloWorldWorkflow':
                                      Subscription(subscriptions=
                                                   {'start': step_sub})})}
        execution_case = case.Case(history=[],
                                   subscriptions=subs,
                                   global_subscriptions=case.GlobalSubscriptions(
                                       step='*',
                                       next_step=['NextStepTaken', 'NextStepNotTaken'],
                                       flag=['FlagArgsValid', 'FlagArgsInvalid'],
                                       filter=['FilterSuccess', 'FilterError']))


        case.addCase(name="testStepFFKEventsEvents", case=execution_case)

        history = case.cases["testStepFFKEventsEvents"]
        with history:
            c.executeWorkflow(name="helloWorldWorkflow")
            self.assertTrue(len(history.history) == 5)
