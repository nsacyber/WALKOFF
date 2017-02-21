import unittest
from core import controller, case, graphDecorator
from tests import config
from core.case import Subscription


class TestExecutionEvents(unittest.TestCase):
    """
            Tests execution Events at the Workflow Level
    """

    def setUp(self):
        case.initialize_case_db()

    def tearDown(self):
        case.case_database.session.rollback()

    @graphDecorator.callgraph(enabled=False)
    def test_workflowExecutionEvents(self):
        c = controller.Controller(name="testExecutionEventsController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "multiactionWorkflowTest.workflow")

        subs = {'testExecutionEventsController':
                    Subscription(subscriptions=
                                 {'multiactionWorkflow':
                                      Subscription(events=["InstanceCreated", "StepExecutionSuccess",
                                                           "NextStepFound", "WorkflowShutdown"])})}

        case.set_subscriptions({'testExecutionEvents': case.CaseSubscriptions(subscriptions=subs)})

        c.executeWorkflow(name="multiactionWorkflow")

        execution_events_case = case.case_database.session.query(case.Cases) \
            .filter(case.Cases.name == 'testExecutionEvents').first()
        execution_event_history = execution_events_case.events.all()
        self.assertTrue(len(execution_event_history) == 6)

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

        case.set_subscriptions({'testStepExecutionEvents': case.CaseSubscriptions(subscriptions=subs)})

        c.executeWorkflow(name="helloWorldWorkflow")

        step_execution_events_case = case.case_database.session.query(case.Cases) \
            .filter(case.Cases.name == 'testStepExecutionEvents').first()
        step_execution_event_history = step_execution_events_case.events.all()
        self.assertTrue(len(step_execution_event_history) == 3)

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

        case.set_subscriptions({'testStepFFKEventsEvents': case.CaseSubscriptions(subscriptions=subs)})

        c.executeWorkflow(name="helloWorldWorkflow")

        step_ffk_events_case = case.case_database.session.query(case.Cases) \
            .filter(case.Cases.name == 'testStepFFKEventsEvents').first()
        step_ffk_event_history = step_ffk_events_case.events.all()
        self.assertTrue(len(step_ffk_event_history) == 6)

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
        global_subs = case.GlobalSubscriptions(step='*',
                                               next_step=['NextStepTaken',
                                                          'NextStepNotTaken'],
                                               flag=['FlagArgsValid',
                                                     'FlagArgsInvalid'],
                                               filter=['FilterSuccess',
                                                       'FilterError'])
        case.set_subscriptions({'testStepFFKEventsEvents': case.CaseSubscriptions(subscriptions=subs,
                                                                                  global_subscriptions=global_subs)})

        c.executeWorkflow(name="helloWorldWorkflow")

        step_ffk_events_case = case.case_database.session.query(case.Cases) \
            .filter(case.Cases.name == 'testStepFFKEventsEvents').first()
        step_ffk_event_history = step_ffk_events_case.events.all()
        self.assertTrue(len(step_ffk_event_history) == 5)
