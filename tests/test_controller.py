import unittest

from core.controller import Controller, _WorkflowKey, initialize_threading, shutdown_pool
from tests import config
from apscheduler.schedulers.gevent import GeventScheduler
import os
from core import helpers
import core.config.config
from tests.apps import App


class TestController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        App.registry = {}
        helpers.import_all_apps(path=config.test_apps_path, reload=True)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.flags = helpers.import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = helpers.import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=config.function_api_path)
        initialize_threading()

    def setUp(self):
        self.controller = Controller()

    @classmethod
    def tearDownClass(cls):
        shutdown_pool()

    def test_create_controller(self):
        self.assertEqual(self.controller.uid, "controller")
        self.assertEqual(self.controller.instances, {})
        self.assertIsNone(self.controller.tree)

    def test_load_workflow_from_file(self):
        path = '{0}{1}.playbook'.format(config.test_workflows_path_with_generated, "test")
        playbook_name = "testPlaybook"
        workflow_name = "helloWorldWorkflow"
        key = _WorkflowKey(playbook_name, workflow_name)
        ret = self.controller.load_workflow_from_file(path=path, workflow_name=workflow_name,
                                                      playbook_override=playbook_name)
        self.assertTrue(ret)
        self.assertTrue(key in self.controller.workflows)

    def test_load_workflows_from_file(self):
        path = config.test_workflows_path + "tieredWorkflow.playbook"
        playbook_name = "testPlaybook"
        self.controller.load_workflows_from_file(path=path, playbook_override=playbook_name)
        key = _WorkflowKey(playbook_name, "parentWorkflow")
        self.assertTrue(key in self.controller.workflows)
        key = _WorkflowKey(playbook_name, "childWorkflow")
        self.assertTrue(key in self.controller.workflows)

    def test_load_all_workflows_from_directory(self):
        path = config.test_workflows_path
        workflows = helpers.locate_workflows_in_directory(path)
        keys = []
        invalid_workflows = ['invalidActionWorkflow', 'invalidAppWorkflow',
                             'tooManyStepInputsWorkflow', 'invalidInputWorkflow']
        for workflow in workflows:
            for name in helpers.get_workflow_names_from_file(os.path.join(config.test_workflows_path, workflow)):
                playbook_name = workflow.split('.')[0]
                if playbook_name not in invalid_workflows:
                    keys.append(_WorkflowKey(playbook_name, name))
        self.controller.load_all_workflows_from_directory(path=path)
        for key in keys:
            self.assertTrue(key in self.controller.workflows)
