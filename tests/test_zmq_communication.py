import threading
import time
import unittest
from os import path
import os
import shutil

from walkoff import initialize_databases
import walkoff.appgateway
import walkoff.config.config
import walkoff.config.paths
import walkoff.controller
from tests import config
from tests.util.case_db_help import *
from tests.util.thread_control import modified_setup_worker_env


class TestZMQCommunication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from walkoff.core.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
        walkoff.config.config.num_processes = 2
        walkoff.config.paths.db_path = config.test_db_path
        walkoff.config.paths.case_db_path = config.test_case_db_path
        walkoff.config.paths.device_db_path = config.test_device_db_path
        initialize_databases()
        pids = spawn_worker_processes(worker_environment_setup=modified_setup_worker_env)
        walkoff.controller.controller.initialize_threading(pids)
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        walkoff.config.config.num_processes = 2

    def setUp(self):
        self.controller = walkoff.controller.controller
        self.controller.workflows = {}
        self.controller.load_playbooks(resource_collection=config.test_workflows_path)
        self.id_tuple = ('simpleDataManipulationWorkflow', 'helloWorldWorkflow')
        self.testWorkflow = self.controller.get_workflow(*self.id_tuple)
        self.testWorkflow.set_execution_uid('some_uid')
        self.start = datetime.utcnow()
        case_database.initialize()

    def tearDown(self):
        self.controller.workflows = None
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

    '''Request and Result Socket Testing (Basic Workflow Execution)'''
    def test_simple_workflow_execution(self):
        workflow = self.controller.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
        setup_subscriptions_for_action(workflow.uid, action_uids)
        self.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.controller.wait_and_reset(1)

        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 1)
        action = actions[0]
        result = action['data']
        self.assertDictEqual(result, {'result': "REPEATING: Hello World", 'status': 'Success'})

    def test_multi_action_workflow(self):
        workflow = self.controller.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        action_names = ['start', '1']
        action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
        setup_subscriptions_for_action(workflow.uid, action_uids)
        self.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

        self.controller.wait_and_reset(1)
        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), 2)
        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'result': "REPEATING: Hello World", 'status': 'Success'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_error_workflow(self):
        workflow = self.controller.get_workflow('multiactionError', 'multiactionErrorWorkflow')
        action_names = ['start', '1', 'error']
        action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
        setup_subscriptions_for_action(workflow.uid, action_uids)
        self.controller.execute_workflow('multiactionError', 'multiactionErrorWorkflow')

        self.controller.wait_and_reset(1)

        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 2)

        expected_results = [{'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                            {'status': 'Success', 'result': 'REPEATING: Hello World'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_workflow_with_dataflow(self):
        workflow = self.controller.get_workflow('dataflowTest', 'dataflowWorkflow')
        action_names = ['start', '1', '2']
        action_uids = [action.uid for action in workflow.actions.values() if action.name in action_names]
        setup_subscriptions_for_action(workflow.uid, action_uids)
        self.controller.execute_workflow('dataflowTest', 'dataflowWorkflow')

        self.controller.wait_and_reset(1)

        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 3)
        expected_results = [{'result': 6, 'status': 'Success'},
                            {'result': 6, 'status': 'Success'},
                            {'result': 15, 'status': 'Success'}]
        for result in [action['data'] for action in actions]:
            self.assertIn(result, expected_results)

    def test_execute_multiple_workflows(self):
        workflow = self.controller.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
        setup_subscriptions_for_action(workflow.uid, action_uids)

        capacity = walkoff.config.config.num_processes * walkoff.config.config.num_threads_per_process

        for i in range(capacity*2):
            self.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        self.controller.wait_and_reset(capacity*2)

        actions = []
        for uid in action_uids:
            actions.extend(executed_actions(uid, self.start, datetime.utcnow()))

        self.assertEqual(len(actions), capacity*2)

    '''Communication Socket Testing'''

    def test_pause_and_resume_workflow(self):
        self.controller.load_playbook(resource=path.join(config.test_workflows_path, 'pauseWorkflowTest.playbook'))

        uid = None
        result = dict()
        result['paused'] = False
        result['resumed'] = False

        def workflow_paused_listener(sender, **kwargs):
            result['paused'] = True
            self.controller.resume_workflow(uid)

        WalkoffEvent.WorkflowPaused.connect(workflow_paused_listener)

        def workflow_resumed_listener(sender, **kwargs):
            result['resumed'] = True

        WalkoffEvent.WorkflowResumed.connect(workflow_resumed_listener)

        def pause_resume_thread():
            self.controller.pause_workflow(uid)
            return

        def action_1_about_to_begin_listener(sender, **kwargs):
            threading.Thread(target=pause_resume_thread).start()
            time.sleep(0)

        WalkoffEvent.WorkflowExecutionStart.connect(action_1_about_to_begin_listener)

        uid = self.controller.execute_workflow('pauseWorkflowTest', 'pauseWorkflow')
        self.controller.wait_and_reset(1)
        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])
