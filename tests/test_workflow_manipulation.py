import socket
import unittest
from os import path

import apps
import walkoff.appgateway
import walkoff.case.database as case_database
import walkoff.case.subscription as case_subscription
import walkoff.config.config
import walkoff.core.controller
import walkoff.core.multiprocessedexecutor
from walkoff.core.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from tests import config
from tests.util.mock_objects import *

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestWorkflowManipulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)
        walkoff.config.config.num_processes = 2
        MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        MultiprocessedExecutor.wait_and_reset = mock_wait_and_reset
        MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool
        walkoff.core.controller.controller.initialize_threading()

    def setUp(self):
        self.controller = walkoff.core.controller.controller
        self.controller.workflows = {}
        self.controller.load_playbooks(
            resource_collection=path.join(".", "tests", "testWorkflows", "testGeneratedWorkflows"))
        self.controller.load_playbook(
            resource=path.join(config.test_workflows_path, 'simpleDataManipulationWorkflow.playbook'))
        self.id_tuple = ('simpleDataManipulationWorkflow', 'helloWorldWorkflow')
        self.testWorkflow = self.controller.get_workflow(*self.id_tuple)
        self.testWorkflow.set_execution_uid('some_uid')
        case_database.initialize()

    def tearDown(self):
        self.controller.workflows = None
        case_database.case_db.tear_down()
        case_subscription.clear_subscriptions()
        reload(socket)

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        walkoff.core.controller.controller.shutdown_pool()

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

        WalkoffEvent.WorkflowExecutionStart.connect(action_1_about_to_begin_listener)

        uid = self.controller.execute_workflow('pauseWorkflowTest', 'pauseWorkflow')
        self.controller.wait_and_reset(1)
        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])

    def test_change_action_input(self):
        arguments = [{'name': 'call', 'value': 'CHANGE INPUT'}]

        result = {'value': None}

        def action_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        WalkoffEvent.ActionExecutionSuccess.connect(action_finished_listener)

        self.controller.execute_workflow('simpleDataManipulationWorkflow', 'helloWorldWorkflow',
                                         start_arguments=arguments)
        self.controller.wait_and_reset(1)
        self.assertDictEqual(result['value'],
                             {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})
