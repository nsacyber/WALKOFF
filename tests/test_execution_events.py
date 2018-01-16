import unittest

import walkoff.appgateway
import walkoff.case.database as case_database
import walkoff.case.subscription as case_subscription
import walkoff.config.config
import walkoff.controller
import walkoff.core.multiprocessedexecutor
from walkoff.core.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from tests import config
from tests.util.mock_objects import *
import tests.config
import walkoff.config.paths
from walkoff import initialize_databases
import walkoff.coredb.devicedb


class TestExecutionEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.config.paths.db_path = tests.config.test_db_path
        walkoff.config.paths.case_db_path = tests.config.test_case_db_path
        walkoff.config.paths.device_db_path = tests.config.test_device_db_path
        initialize_databases()
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        walkoff.controller.controller.initialize_threading()

    def setUp(self):
        self.c = walkoff.controller.controller
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tear_down()

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        walkoff.controller.controller.shutdown_pool()

    def test_workflow_execution_events(self):
        # self.c.load_playbook(resource=config.test_workflows_path + 'multiactionWorkflowTest.playbook')
        workflow_id = self.c.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow').id
        subs = {'case1': {workflow_id: [WalkoffEvent.AppInstanceCreated.signal_name,
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
        # self.c.load_playbook(resource=config.test_workflows_path + 'basicWorkflowTest.playbook')
        workflow = self.c.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action_ids = [action.id for action in workflow.actions]
        action_events = [WalkoffEvent.ActionExecutionSuccess.signal_name, WalkoffEvent.ActionStarted.signal_name]
        subs = {'case1': {action_uid: action_events for action_uid in action_ids}}
        case_subscription.set_subscriptions(subs)

        self.c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.c.wait_and_reset(1)

        execution_events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(execution_events), 2,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(2, len(execution_events)))

    # TODO: Rewrite this test. This workflow has no branches because there is only one action.
    # def test_condition_transform_execution_events(self):
    #     # self.c.load_playbook(resource=config.test_workflows_path + 'basicWorkflowTest.playbook')
    #     workflow = self.c.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #     action_id = None
    #     for action in workflow.actions:
    #         if action.name == 'repeatBackToMe':
    #             action_id = action.id
    #
    #     subs = {action_id: [WalkoffEvent.ActionExecutionSuccess.signal_name, WalkoffEvent.ActionStarted.signal_name]}
    #     branch = workflow.branches[0]
    #     subs[branch.id] = [WalkoffEvent.BranchTaken.signal_name, WalkoffEvent.BranchNotTaken.signal_name]
    #     condition = next(condition for condition in branch.conditions if condition.action_name == 'regMatch')
    #     subs[condition.id] = [WalkoffEvent.ConditionSuccess.signal_name, WalkoffEvent.ConditionError.signal_name]
    #     transform = next(transform for transform in condition.transforms if transform.action_name == 'length')
    #     subs[transform.id] = [WalkoffEvent.TransformSuccess.signal_name, WalkoffEvent.TransformError.signal_name]
    #
    #     case_subscription.set_subscriptions({'case1': subs})
    #
    #     self.c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #
    #     self.c.wait_and_reset(1)
    #
    #     events = case_database.case_db.session.query(case_database.Case) \
    #         .filter(case_database.Case.name == 'case1').first().events.all()
    #     self.assertEqual(len(events), 5,
    #                      'Incorrect length of event history. '
    #                      'Expected {0}, got {1}'.format(5, len(events)))
