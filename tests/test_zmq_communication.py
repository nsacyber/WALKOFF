import os
import shutil
import threading
import time
import unittest
from datetime import datetime

import walkoff.appgateway
import walkoff.config.config
import walkoff.config.paths
from tests import config
from tests.util import execution_db_help
from tests.util.case_db_help import *
from tests.util.thread_control import modified_setup_worker_env
from walkoff import executiondb
from walkoff.executiondb.workflowresults import WorkflowStatus, WorkflowStatusEnum
from walkoff.multiprocessedexecutor.multiprocessedexecutor import multiprocessedexecutor
from walkoff.server import workflowresults  # Need this import
import walkoff.cache


class TestZMQCommunication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()
        walkoff.cache.make_cache()

        from walkoff.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
        walkoff.config.config.num_processes = 2
        pids = spawn_worker_processes(worker_environment_setup=modified_setup_worker_env)
        multiprocessedexecutor.initialize_threading(pids)
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        walkoff.config.config.num_processes = 2

    def setUp(self):
        self.start = datetime.utcnow()
        case_database.initialize()

    def tearDown(self):
        execution_db_help.cleanup_device_db()
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
        multiprocessedexecutor.shutdown_pool()
        execution_db_help.tear_down_device_db()

    '''Request and Result Socket Testing (Basic Workflow Execution)'''

    def test_simple_workflow_execution(self):
        workflow = execution_db_help.load_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)
        multiprocessedexecutor.execute_workflow(workflow.id)

        multiprocessedexecutor.wait_and_reset(1)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 1)
        action = actions[0]
        result = action['data']
        self.assertDictEqual(result, {'result': "REPEATING: Hello World", 'status': 'Success'})

    def test_multi_action_workflow(self):
        workflow = execution_db_help.load_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        action_names = ['start', '1']
        action_ids = [action.id for action in workflow.actions if action.name in action_names]
        setup_subscriptions_for_action(workflow.id, action_ids)
        multiprocessedexecutor.execute_workflow(workflow.id)

        multiprocessedexecutor.wait_and_reset(1)
        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 2)
        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'result': "REPEATING: Hello World", 'status': 'Success'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_error_workflow(self):
        workflow = execution_db_help.load_workflow('multiactionError', 'multiactionErrorWorkflow')
        action_names = ['start', '1', 'error']
        action_ids = [action.id for action in workflow.actions if action.name in action_names]
        setup_subscriptions_for_action(workflow.id, action_ids)
        multiprocessedexecutor.execute_workflow(workflow.id)

        multiprocessedexecutor.wait_and_reset(1)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 2)

        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'status': 'Success', 'result': 'REPEATING: Hello World'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_workflow_with_dataflow(self):
        workflow = execution_db_help.load_workflow('dataflowTest', 'dataflowWorkflow')
        action_names = ['start', '1', '2']
        action_ids = [action.id for action in workflow.actions if action.name in action_names]
        setup_subscriptions_for_action(workflow.id, action_ids)
        multiprocessedexecutor.execute_workflow(workflow.id)

        multiprocessedexecutor.wait_and_reset(1)

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
        workflow = execution_db_help.load_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)

        capacity = walkoff.config.config.num_processes * walkoff.config.config.num_threads_per_process

        for i in range(capacity * 2):
            multiprocessedexecutor.execute_workflow(workflow.id)

        multiprocessedexecutor.wait_and_reset(capacity * 2)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), capacity * 2)

    '''Communication Socket Testing'''

    def test_pause_and_resume_workflow(self):
        execution_id = None
        result = dict()
        result['paused'] = False
        result['resumed'] = False

        def pause_resume_thread():
            multiprocessedexecutor.pause_workflow(execution_id)
            return

        @WalkoffEvent.WorkflowPaused.connect
        def workflow_paused_listener(sender, **kwargs):
            result['paused'] = True
            wf_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
                execution_id=sender['execution_id']).first()
            wf_status.paused()
            executiondb.execution_db.session.commit()

            multiprocessedexecutor.resume_workflow(execution_id)

        @WalkoffEvent.WorkflowResumed.connect
        def workflow_resumed_listener(sender, **kwargs):
            result['resumed'] = True

        workflow = execution_db_help.load_workflow('pauseResumeWorkflowFixed', 'pauseResumeWorkflow')
        action_ids = [action.id for action in workflow.actions]
        workflow_events = ['Workflow Paused', 'Workflow Resumed']
        setup_subscriptions_for_action(workflow.id, action_ids, workflow_events=workflow_events)

        execution_id = multiprocessedexecutor.execute_workflow(workflow.id)

        while True:
            executiondb.execution_db.session.expire_all()
            workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
                execution_id=execution_id).first()
            if workflow_status and workflow_status.status == WorkflowStatusEnum.running:
                threading.Thread(target=pause_resume_thread).start()
                time.sleep(0)
                break

        multiprocessedexecutor.wait_and_reset(1)
        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))

        self.assertGreaterEqual(len(actions), 1)
        self.assertEqual(actions[-1]['data']['result'], 'success')
