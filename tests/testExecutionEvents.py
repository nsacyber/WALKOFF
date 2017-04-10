import unittest

import core.case.database as case_database
import core.case.subscription as case_subscription
from core import controller, graphdecorator
from core.case.subscription import Subscription
from core.helpers import construct_workflow_name_key
from tests import config
from server.flaskserver import running_context


class TestExecutionEvents(unittest.TestCase):
    """
            Tests execution Events at the Workflow Level
    """

    def setUp(self):
        case_database.initialize()
        running_context.init_threads()

    def tearDown(self):
        case_database.tearDown()

    @graphdecorator.callgraph(enabled=False)
    def test_workflowExecutionEvents(self):
        workflow_name = construct_workflow_name_key('multiactionWorkflowTest', 'multiactionWorkflow')
        c = controller.Controller(name="testExecutionEventsController")
        c.load_workflows_from_file(path=config.test_workflows_path + "multiactionWorkflowTest.workflow")

        subs = {'testExecutionEventsController':
                    Subscription(subscriptions=
                                 {workflow_name:
                                      Subscription(events=["InstanceCreated", "StepExecutionSuccess",
                                                           "NextStepFound", "WorkflowShutdown"])})}

        case_subscription.set_subscriptions(
            {'testExecutionEvents': case_subscription.CaseSubscriptions(subscriptions=subs)})

        c.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

        running_context.shutdown_threads()

        execution_events_case = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'testExecutionEvents').first()
        execution_event_history = execution_events_case.events.all()
        self.assertEqual(len(execution_event_history), 6,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(6, len(execution_event_history)))

    """
        Tests execution events at the Step Level
    """

    @graphdecorator.callgraph(enabled=False)
    def test_stepExecutionEvents(self):
        workflow_name = construct_workflow_name_key('basicWorkflowTest', 'helloWorldWorkflow')
        c = controller.Controller(name="testStepExecutionEventsController")
        c.load_workflows_from_file(path=config.test_workflows_path + "basicWorkflowTest.workflow")

        subs = {'testStepExecutionEventsController':
            Subscription(subscriptions=
            {workflow_name:
                Subscription(subscriptions=
                {'start':
                    Subscription(
                        events=["FunctionExecutionSuccess", "InputValidated",
                                "ConditionalsExecuted"])})})}

        case_subscription.set_subscriptions(
            {'testStepExecutionEvents': case_subscription.CaseSubscriptions(subscriptions=subs)})

        c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        running_context.shutdown_threads()

        step_execution_events_case = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'testStepExecutionEvents').first()
        step_execution_event_history = step_execution_events_case.events.all()
        self.assertEqual(len(step_execution_event_history), 3,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(3, len(step_execution_event_history)))

    """
        Tests execution events at the Filter Flag and Keyword Level
    """

    @graphdecorator.callgraph(enabled=False)
    def test_ffkExecutionEvents(self):
        workflow_name = construct_workflow_name_key('basicWorkflowTest', 'helloWorldWorkflow')
        c = controller.Controller(name="testStepFFKEventsController")
        c.load_workflows_from_file(path=config.test_workflows_path + "basicWorkflowTest.workflow")

        filter_sub = Subscription(events=['FilterSuccess', 'FilterError'])
        flag_sub = Subscription(events=['FlagArgsValid', 'FlagArgsInvalid'], subscriptions={'length': filter_sub})
        next_sub = Subscription(events=['NextStepTaken', 'NextStepNotTaken'], subscriptions={'regMatch': flag_sub})
        step_sub = Subscription(events=["FunctionExecutionSuccess", "InputValidated", "ConditionalsExecuted"],
                                subscriptions={'1': next_sub})
        subs = {'testStepFFKEventsController':
                    Subscription(subscriptions=
                                 {workflow_name:
                                      Subscription(subscriptions=
                                                   {'start': step_sub})})}

        case_subscription.set_subscriptions(
            {'testStepFFKEventsEvents': case_subscription.CaseSubscriptions(subscriptions=subs)})

        c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        running_context.shutdown_threads()

        step_ffk_events_case = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'testStepFFKEventsEvents').first()
        step_ffk_event_history = step_ffk_events_case.events.all()
        self.assertEqual(len(step_ffk_event_history), 6,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(6, len(step_ffk_event_history)))

    @graphdecorator.callgraph(enabled=False)
    def test_ffkExecutionEventsCase(self):
        c = controller.Controller(name="testStepFFKEventsController")
        c.load_workflows_from_file(path=config.test_workflows_path + "basicWorkflowTest.workflow")
        workflow_name = construct_workflow_name_key('basicWorkflowTest', 'helloWorldWorkflow')
        filter_sub = Subscription(events=['FilterError'])
        flag_sub = Subscription(events=['FlagArgsValid',
                                        'FlagArgsInvalid'], subscriptions={'length': filter_sub})
        next_sub = Subscription(events=['NextStepTaken',
                                        'NextStepNotTaken'],
                                subscriptions={'regMatch': flag_sub})
        step_sub = Subscription(events=['FunctionExecutionSuccess',
                                        'InputValidated',
                                        'ConditionalsExecuted'], subscriptions={'1': next_sub})
        subs = {'testStepFFKEventsController':
                    Subscription(subscriptions=
                                 {workflow_name:
                                      Subscription(subscriptions=
                                                   {'start': step_sub})})}
        global_subs = case_subscription.GlobalSubscriptions(step=['FunctionExecutionSuccess',
                                                                  'InputValidated',
                                                                  'ConditionalsExecuted'],
                                                            next_step=['NextStepTaken',
                                                                       'NextStepNotTaken'],
                                                            flag=['FlagArgsValid',
                                                                  'FlagArgsInvalid'],
                                                            filter=['FilterError'])
        case_subscription.set_subscriptions(
            {'testStepFFKEventsEvents': case_subscription.CaseSubscriptions(subscriptions=subs,
                                                                            global_subscriptions=global_subs)})

        c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        running_context.shutdown_threads()

        step_ffk_events_case = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'testStepFFKEventsEvents').first()
        step_ffk_event_history = step_ffk_events_case.events.all()
        self.assertEqual(len(step_ffk_event_history), 5,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(5, len(step_ffk_event_history)))
        step_json = [step.as_json() for step in step_ffk_event_history if step.as_json()['message'] == 'STEP']
        for step in step_json:
            if step['type'] == 'Function executed successfully':
                self.assertDictEqual(step['data'], {'result': 'REPEATING: Hello World'})
            else:
                self.assertEqual(step['data'], '')