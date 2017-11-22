import unittest

import apps
import core.case.database as case_database
import core.case.subscription as case_subscription
import core.config.config
import core.controller
import core.loadbalancer
from core.events import WalkoffEvent
import core.multiprocessedexecutor
from tests import config
from tests.util.mock_objects import *


class TestExecutionEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(config.test_apps_path)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.multiprocessedexecutor.MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        core.multiprocessedexecutor.MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        core.multiprocessedexecutor.MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        core.controller.controller.initialize_threading()

    def setUp(self):
        self.c = core.controller.controller
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tear_down()

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()
        core.controller.controller.shutdown_pool()

    def test_workflow_execution_events(self):

        self.c.load_playbook(resource=config.test_workflows_path + 'multiactionWorkflowTest.playbook')
        workflow_uid = self.c.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow').uid
        subs = {'case1': {workflow_uid: [WalkoffEvent.AppInstanceCreated.signal_name,
                                         WalkoffEvent.WorkflowShutdown.signal_name]}}
        case_subscription.set_subscriptions(subs)
        self.c.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

        self.c.wait_and_reset(1)
        execution_events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()

        self.assertEqual(len(execution_events), 2,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(2, len(execution_events)))

    def test_action_execution_events(self):
        self.c.load_playbook(resource=config.test_workflows_path + 'basicWorkflowTest.playbook')
        workflow = self.c.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action_uids = [action.uid for action in workflow.actions.values()]
        action_events = [WalkoffEvent.ActionExecutionSuccess.signal_name, WalkoffEvent.ActionStarted.signal_name]
        subs = {'case1': {action_uid: action_events for action_uid in action_uids}}
        case_subscription.set_subscriptions(subs)

        self.c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.c.wait_and_reset(1)

        execution_events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(execution_events), 2,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(2, len(execution_events)))

    def test_condition_transform_execution_events(self):
        self.c.load_playbook(resource=config.test_workflows_path + 'basicWorkflowTest.playbook')
        workflow = self.c.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action = workflow.actions['c5a7c29a0f844b69a59901bb542e9305']
        subs = {action.uid: [WalkoffEvent.ActionExecutionSuccess.signal_name, WalkoffEvent.ActionStarted.signal_name]}
        branches = [branch for sublist in workflow.branches.values() for branch in sublist]
        branch = branches[0]
        subs[branch.uid] = [WalkoffEvent.BranchTaken.signal_name, WalkoffEvent.BranchNotTaken.signal_name]
        condition = next(condition for condition in branch.conditions if condition.action_name == 'regMatch')
        subs[condition.uid] = [WalkoffEvent.ConditionSuccess.signal_name, WalkoffEvent.ConditionError.signal_name]
        transform = next(transform for transform in condition.transforms if transform.action_name == 'length')
        subs[transform.uid] = [WalkoffEvent.TransformSuccess.signal_name, WalkoffEvent.TransformError.signal_name]

        case_subscription.set_subscriptions({'case1': subs})

        self.c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.c.wait_and_reset(1)

        events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(events), 5,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(5, len(events)))
