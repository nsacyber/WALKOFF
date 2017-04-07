import unittest

from core.controller import Controller, _WorkflowKey
from core.config import paths
from tests import config
from apscheduler.schedulers.gevent import GeventScheduler
from os import sep
import os
from core import helpers


class TestController(unittest.TestCase):
    def setUp(self):
        self.controller = Controller(name="testController")

    def test_create_controller(self):
        self.assertEqual(self.controller.name, "testController")
        self.assertEqual(self.controller.instances, {})
        self.assertIsNone(self.controller.tree)
        self.assertIsInstance(self.controller.scheduler, GeventScheduler)
        self.assertEqual(self.controller.ancestry, ["testController"])

    def test_load_workflow_from_file(self):
        path = '{0}{1}{2}.workflow'.format(paths.workflows_path, sep, "test")
        playbook_name = "testPlaybook"
        workflow_name = "helloWorldWorkflow"
        key = _WorkflowKey(playbook_name, workflow_name)
        ret = self.controller.load_workflow_from_file(path=path, workflow_name=workflow_name, playbook_override=playbook_name)
        self.assertTrue(ret)
        self.assertTrue(key in self.controller.workflows)

    def test_load_workflows_from_file(self):
        path = config.test_workflows_path + "tieredWorkflow.workflow"
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
        for workflow in workflows:
            for name in helpers.get_workflow_names_from_file(os.path.join(config.test_workflows_path, workflow)):
                playbook_name = workflow.split('.')[0]
                keys.append(_WorkflowKey(playbook_name, name))
        self.controller.load_all_workflows_from_directory(path=path)
        for key in keys:
            self.assertTrue(key in self.controller.workflows)
