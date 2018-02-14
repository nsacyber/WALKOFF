import threading
import time
import unittest
import os
import shutil

import walkoff.appgateway
import walkoff.config.config
import walkoff.config.paths
import walkoff.controller
from tests import config
from tests.util.case_db_help import *
from tests.util.thread_control import modified_setup_worker_env
from tests.util import device_db_help
from walkoff.coredb.workflowresults import WorkflowStatus, ActionStatus
from walkoff.coredb import devicedb
from walkoff.server import workflowresults  # Need this import


class TestZMQCommunication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        device_db_help.setup_dbs()

        from walkoff.core.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
        walkoff.config.config.num_processes = 2
        pids = spawn_worker_processes(worker_environment_setup=modified_setup_worker_env)
        walkoff.controller.controller.initialize_threading(pids)
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        walkoff.config.config.num_processes = 2

    def setUp(self):
        self.controller = walkoff.controller.controller
        self.start = datetime.utcnow()
        case_database.initialize()

    def tearDown(self):
        device_db_help.cleanup_device_db()
        case_database.case_db.tear_down()
        case_subscription.clear_subscriptions()

    @classmethod
    def tearDownClass(cls):
        if config.test_data_path in os.listdir(config.test_path):
            if os.path.isfile(config.test_data_path):
                os.remove(config.test_data_path)
            else:
                shutil.rmtree(config.test_data_path)
        walkoff.appgateway.clear_cache()
        walkoff.controller.controller.shutdown_pool()
        device_db_help.tear_down_device_db()

    '''Request and Result Socket Testing (Basic Workflow Execution)'''
    def test_simple_workflow_execution(self):
        workflow = device_db_help.load_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)
        self.controller.execute_workflow(workflow.id)

        self.controller.wait_and_reset(1)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 1)
        action = actions[0]
        result = action['data']
        self.assertDictEqual(result, {'result': "REPEATING: Hello World", 'status': 'Success'})

    def test_multi_action_workflow(self):
        workflow = device_db_help.load_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        action_names = ['start', '1']
        action_ids = [action.id for action in workflow.actions if action.name in action_names]
        setup_subscriptions_for_action(workflow.id, action_ids)
        self.controller.execute_workflow(workflow.id)

        self.controller.wait_and_reset(1)
        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 2)
        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'result': "REPEATING: Hello World", 'status': 'Success'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_error_workflow(self):
        workflow = device_db_help.load_workflow('multiactionError', 'multiactionErrorWorkflow')
        action_names = ['start', '1', 'error']
        action_ids = [action.id for action in workflow.actions if action.name in action_names]
        setup_subscriptions_for_action(workflow.id, action_ids)
        self.controller.execute_workflow(workflow.id)

        self.controller.wait_and_reset(1)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 2)

        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'status': 'Success', 'result': 'REPEATING: Hello World'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_workflow_with_dataflow(self):
        workflow = device_db_help.load_workflow('dataflowTest', 'dataflowWorkflow')
        action_names = ['start', '1', '2']
        action_ids = [action.id for action in workflow.actions if action.name in action_names]
        setup_subscriptions_for_action(workflow.id, action_ids)
        self.controller.execute_workflow(workflow.id)

        self.controller.wait_and_reset(1)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 3)
        expected_results = [{'result': 6, 'status': 'Success'},
                            {'result': 6, 'status': 'Success'},
                            {'result': 15, 'status': 'Success'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_execute_multiple_workflows(self):
        workflow = device_db_help.load_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)

        capacity = walkoff.config.config.num_processes * walkoff.config.config.num_threads_per_process

        for i in range(capacity*2):
            self.controller.execute_workflow(workflow.id)

        self.controller.wait_and_reset(capacity*2)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), capacity*2)

    '''Communication Socket Testing'''
    def test_pause_and_resume_workflow(self):
        execution_id = None
        result = dict()
        result['paused'] = False
        result['resumed'] = False

        @WalkoffEvent.ActionExecutionSuccess.connect
        def action_1_about_to_begin_listener(sender, **kwargs):
            if not result['resumed']:
                threading.Thread(target=pause_resume_thread).start()
                time.sleep(0)

        def pause_resume_thread():
            self.controller.pause_workflow(execution_id)
            return

        @WalkoffEvent.WorkflowPaused.connect
        def workflow_paused_listener(sender, **kwargs):
            workflow_status = devicedb.device_db.session.query(WorkflowStatus).filter_by(
                execution_id=sender['workflow_execution_id']).first()
            workflow_status.paused()
            action_status = devicedb.device_db.session.query(ActionStatus).filter_by(
                _workflow_status_id=sender['workflow_execution_id']).first()
            action_status.paused()
            devicedb.device_db.session.commit()

            result['paused'] = True
            self.controller.resume_workflow(execution_id)

        @WalkoffEvent.WorkflowResumed.connect
        def workflow_resumed_listener(sender, **kwargs):
            result['resumed'] = True

        workflow = device_db_help.load_workflow('testGeneratedWorkflows/pauseWorkflowTest', 'pauseWorkflow')
        action_ids = [action.id for action in workflow.actions]
        setup_subscriptions_for_action(workflow.id, action_ids)

        execution_id = self.controller.execute_workflow(workflow.id)
        self.controller.wait_and_reset(1)
        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 3)
