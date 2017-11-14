import socket
import unittest
from os import path

import apps
import core.case.database as case_database
import core.case.subscription as case_subscription
import core.config.config
import core.controller
import core.loadbalancer
import core.multiprocessedexecutor
from core.case.callbacks import FunctionExecutionSuccess, WorkflowExecutionStart, WorkflowPaused, WorkflowResumed
from core.executionelements.step import Step
from core.executionelements.workflow import Workflow
from core.appinstance import AppInstance
from tests import config
from tests.util.mock_objects import *

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestWorkflowManipulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(config.test_apps_path)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.num_processes = 2
        core.multiprocessedexecutor.MultiprocessedExecutor.initialize_threading = mock_initialize_threading
        core.multiprocessedexecutor.MultiprocessedExecutor.shutdown_pool = mock_shutdown_pool

    def setUp(self):
        self.controller = core.controller.controller
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
        self.controller.shutdown_pool(0)
        reload(socket)

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def test_simple_risk(self):
        workflow = Workflow(name='workflow')
        workflow.create_step(name="stepOne", action='helloWorld', app='HelloWorld', risk=1)
        workflow.create_step(name="stepTwo", action='helloWorld', app='HelloWorld', risk=2)
        workflow.create_step(name="stepThree", action='helloWorld', app='HelloWorld', risk=3)

        self.assertEqual(workflow._total_risk, 6)

    def test_accumulated_risk_with_error(self):
        workflow = Workflow(name='workflow')
        workflow._execution_uid = 'some_uid'
        step1 = Step(name="step_one", app='HelloWorld', action='Buggy', risk=1)
        step2 = Step(name="step_two", app='HelloWorld', action='Buggy', risk=2)
        step3 = Step(name="step_three", app='HelloWorld', action='Buggy', risk=3.5)
        workflow.steps = {'step_one': step1, 'step_two': step2, 'step_three': step3}
        workflow._total_risk = 6.5

        instance = AppInstance.create(app_name='HelloWorld', device_name='test_device_name')

        workflow._Workflow__execute_step(workflow.steps["step_one"], instance)
        self.assertAlmostEqual(workflow.accumulated_risk, 1.0 / 6.5)
        workflow._Workflow__execute_step(workflow.steps["step_two"], instance)
        self.assertAlmostEqual(workflow.accumulated_risk, (1.0 / 6.5) + (2.0 / 6.5))
        workflow._Workflow__execute_step(workflow.steps["step_three"], instance)
        self.assertAlmostEqual(workflow.accumulated_risk, 1.0)

    def test_pause_and_resume_workflow(self):
        self.controller.initialize_threading()
        self.controller.load_playbook(resource=path.join(config.test_workflows_path, 'pauseWorkflowTest.playbook'))

        uid = None
        result = dict()
        result['paused'] = False
        result['resumed'] = False

        @WorkflowPaused.connect
        def workflow_paused_listener(sender, **kwargs):
            result['paused'] = True
            self.controller.resume_workflow(uid)

        @WorkflowResumed.connect
        def workflow_resumed_listener(sender, **kwargs):
            result['resumed'] = True

        def pause_resume_thread():
            self.controller.pause_workflow(uid)
            return

        @WorkflowExecutionStart.connect
        def step_1_about_to_begin_listener(sender, **kwargs):
            threading.Thread(target=pause_resume_thread).start()

        uid = self.controller.execute_workflow('pauseWorkflowTest', 'pauseWorkflow')
        self.controller.shutdown_pool(1)
        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])

    def test_change_step_input(self):
        self.controller.initialize_threading()
        arguments = [{'name': 'call', 'value': 'CHANGE INPUT'}]

        result = {'value': None}

        def step_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        FunctionExecutionSuccess.connect(step_finished_listener)

        self.controller.execute_workflow('simpleDataManipulationWorkflow', 'helloWorldWorkflow',
                                         start_arguments=arguments)
        self.controller.shutdown_pool(1)
        self.assertDictEqual(result['value'],
                             {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})
