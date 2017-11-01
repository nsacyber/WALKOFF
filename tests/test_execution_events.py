import unittest

import apps
import core.case.database as case_database
import core.case.subscription as case_subscription
import core.config.config
import core.controller
import core.loadbalancer
import core.multiprocessedexecutor
from tests import config
from tests.util.mock_objects import *


class TestExecutionEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(config.test_apps_path)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.multiprocessedexecutor.MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        core.multiprocessedexecutor.MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool

    def setUp(self):
        self.c = core.controller.controller
        self.c.initialize_threading()
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tear_down()

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def test_workflow_execution_events(self):

        self.c.load_playbook(resource=config.test_workflows_path + 'multiactionWorkflowTest.playbook')
        workflow_uid = self.c.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow').uid
        subs = {'case1': {workflow_uid: ['App Instance Created', 'Step Execution Success',
                                         'Next Step Found', 'Workflow Shutdown']}}
        case_subscription.set_subscriptions(subs)
        self.c.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

        self.c.shutdown_pool(1)
        execution_events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()

        self.assertEqual(len(execution_events), 6,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(6, len(execution_events)))

    def test_step_execution_events(self):
        self.c.load_playbook(resource=config.test_workflows_path + 'basicWorkflowTest.playbook')
        workflow = self.c.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        step_uids = [step.uid for step in workflow.steps.values()]
        step_events = ['Function Execution Success', 'Step Started', 'Conditionals Executed']
        subs = {'case1': {step_uid: step_events for step_uid in step_uids}}
        case_subscription.set_subscriptions(subs)

        self.c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.c.shutdown_pool(1)

        execution_events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(execution_events), 3,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(3, len(execution_events)))

    def test_condition_transform_execution_events(self):
        self.c.load_playbook(resource=config.test_workflows_path + 'basicWorkflowTest.playbook')
        workflow = self.c.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        step = workflow.steps['c5a7c29a0f844b69a59901bb542e9305']
        subs = {step.uid: ['Function Execution Success', 'Step Started', 'Conditionals Executed']}
        next_step = next(conditional for conditional in step.next_steps if conditional.name == '1')
        subs[next_step.uid] = ['Next Step Taken', 'Next Step Not Taken']
        condition = next(condition for condition in next_step.conditions if condition.action == 'regMatch')
        subs[condition.uid] = ['Condition Success', 'Condition Error']
        transform = next(transform for transform in condition.transforms if transform.action == 'length')
        subs[transform.uid] = ['Transform Success', 'Transform Error']

        case_subscription.set_subscriptions({'case1': subs})

        self.c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.c.shutdown_pool(1)

        events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(events), 6,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(6, len(events)))
