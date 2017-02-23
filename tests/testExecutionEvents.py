import unittest

import core.case.database as case_database
import core.case.subscription as case_subscription
from core import controller, graphDecorator
from core.case.subscription import Subscription
from tests import config


class TestExecutionEvents(unittest.TestCase):
    """
            Tests execution Events at the Workflow Level
    """

    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tearDown()

    @graphDecorator.callgraph(enabled=False)
    def test_workflowExecutionEvents(self):
        c = controller.Controller(name="testExecutionEventsController")
        c.loadWorkflowsFromFile(path=config.testWorkflowsPath + "multiactionWorkflowTest.workflow")

        subs = {'testExecutionEventsController':
                    Subscription(subscriptions=
                                 {'multiactionWorkflow':
                                      Subscription(events=["InstanceCreated", "StepExecutionSuccess",
                                                           "NextStepFound", "WorkflowShutdown"])})}

        case_subscription.set_subscriptions(
            {'testExecutionEvents': case_subscription.CaseSubscriptions(subscriptions=subs)})

        c.executeWorkflow(name="multiactionWorkflow")

        execution_events_case = case_database.case_db.session.query(case_database.Cases) \
            .filter(case_database.Cases.name == 'testExecutionEvents').first()
        execution_event_history = execution_events_case.events.all()
        self.assertEqual(len(execution_event_history), 6,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(6, len(execution_event_history)))

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

        case_subscription.set_subscriptions(
            {'testStepExecutionEvents': case_subscription.CaseSubscriptions(subscriptions=subs)})

        c.executeWorkflow(name="helloWorldWorkflow")

        step_execution_events_case = case_database.case_db.session.query(case_database.Cases) \
            .filter(case_database.Cases.name == 'testStepExecutionEvents').first()
        step_execution_event_history = step_execution_events_case.events.all()
        self.assertEqual(len(step_execution_event_history), 3,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(3, len(step_execution_event_history)))

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

        case_subscription.set_subscriptions(
            {'testStepFFKEventsEvents': case_subscription.CaseSubscriptions(subscriptions=subs)})

        c.executeWorkflow(name="helloWorldWorkflow")

        step_ffk_events_case = case_database.case_db.session.query(case_database.Cases) \
            .filter(case_database.Cases.name == 'testStepFFKEventsEvents').first()
        step_ffk_event_history = step_ffk_events_case.events.all()
        self.assertEqual(len(step_ffk_event_history), 6,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(6, len(step_ffk_event_history)))

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
        global_subs = case_subscription.GlobalSubscriptions(step='*',
                                                            next_step=['NextStepTaken',
                                                                       'NextStepNotTaken'],
                                                            flag=['FlagArgsValid',
                                                                  'FlagArgsInvalid'],
                                                            filter=['FilterSuccess',
                                                                    'FilterError'])
        case_subscription.set_subscriptions(
            {'testStepFFKEventsEvents': case_subscription.CaseSubscriptions(subscriptions=subs,
                                                                            global_subscriptions=global_subs)})

        c.executeWorkflow(name="helloWorldWorkflow")

        step_ffk_events_case = case_database.case_db.session.query(case_database.Cases) \
            .filter(case_database.Cases.name == 'testStepFFKEventsEvents').first()
        step_ffk_event_history = step_ffk_events_case.events.all()
        self.assertEqual(len(step_ffk_event_history), 5,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(5, len(step_ffk_event_history)))
