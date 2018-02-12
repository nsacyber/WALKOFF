import socket
import unittest

import walkoff.appgateway
import walkoff.config.config
import walkoff.controller
import walkoff.core.multiprocessedexecutor
from walkoff.core.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from tests import config
from tests.util.mock_objects import *
import walkoff.config.paths
from tests.util import device_db_help
from walkoff.coredb import devicedb
from walkoff.coredb.argument import Argument
from walkoff.coredb.workflowresults import WorkflowStatus, ActionStatus
from tests.util.case_db_help import *
from walkoff.server import workflowresults  # Need this import

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestWorkflowManipulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        device_db_help.setup_dbs()

        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        walkoff.config.config.num_processes = 2
        MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        walkoff.controller.controller.initialize_threading()

    def setUp(self):
        self.controller = walkoff.controller.controller
        self.start = datetime.utcnow()
        case_database.initialize()

    def tearDown(self):
        device_db_help.cleanup_device_db()
        case_database.case_db.tear_down()
        case_subscription.clear_subscriptions()
        reload(socket)

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        walkoff.controller.controller.shutdown_pool()
        device_db_help.tear_down_device_db()

    # TODO: Delete this test -- pause/resume is already being tested.
    # def test_pause_and_resume_workflow(self):
    #     execution_id = None
    #     result = dict()
    #     result['paused'] = False
    #     result['resumed'] = False
    #
    #     @WalkoffEvent.WorkflowExecutionStart.connect
    #     def action_1_about_to_begin_listener(sender, **kwargs):
    #         if not result['resumed']:
    #             threading.Thread(target=pause_resume_thread).start()
    #
    #     def pause_resume_thread():
    #         self.controller.pause_workflow(execution_id)
    #         return
    #
    #     @WalkoffEvent.WorkflowPaused.connect
    #     def workflow_paused_listener(sender, **kwargs):
    #         workflow_status = devicedb.device_db.session.query(WorkflowStatus).filter_by(
    #             execution_id=sender['workflow_execution_id']).first()
    #         workflow_status.paused()
    #         action_status = devicedb.device_db.session.query(ActionStatus).filter_by(
    #             _workflow_status_id=sender['workflow_execution_id']).first()
    #
    #         if action_status:
    #             action_status.paused()
    #         devicedb.device_db.session.commit()
    #
    #         result['paused'] = True
    #         self.controller.resume_workflow(execution_id)
    #
    #     @WalkoffEvent.WorkflowResumed.connect
    #     def workflow_resumed_listener(sender, **kwargs):
    #         result['resumed'] = True
    #
    #     workflow = device_db_help.load_workflow('testGeneratedWorkflows/pauseWorkflowTest', 'pauseWorkflow')
    #     action_ids = [action.id for action in workflow.actions]
    #     setup_subscriptions_for_action(workflow.id, action_ids)
    #
    #     execution_id = self.controller.execute_workflow(workflow.id)
    #     self.controller.wait_and_reset(1)
    #     self.assertTrue(result['paused'])
    #     self.assertTrue(result['resumed'])
    #
    #     actions = []
    #     for id_ in action_ids:
    #         actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
    #
    #     self.assertEqual(len(actions), 3)

    def test_change_action_input(self):
        arguments = [Argument(name='call', value='CHANGE INPUT')]

        result = {'value': None}

        def action_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        WalkoffEvent.ActionExecutionSuccess.connect(action_finished_listener)

        workflow = device_db_help.load_workflow('simpleDataManipulationWorkflow', 'helloWorldWorkflow')

        self.controller.execute_workflow(workflow.id, start_arguments=arguments)
        self.controller.wait_and_reset(1)
        self.assertDictEqual(result['value'],
                             {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})
