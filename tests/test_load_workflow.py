import unittest

import apps
import walkoff.config.config
from walkoff.core import controller
from tests import config
from tests.config import test_apps_path


class TestLoadWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=test_apps_path)

    def setUp(self):
        self.c = controller.Controller()
        self.c.load_playbook(resource=config.test_workflows_path + 'basicWorkflowTest.playbook')
        self.testWorkflow = self.c.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        self.workflow_uid = "c5a7c29a0f844b69a59901bb542e9305"

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def test_workflow_loaded(self):
        # Tests that helloWorldWorkflow exists
        self.assertTrue(self.c.is_workflow_registered('basicWorkflowTest', 'helloWorldWorkflow'))

    def test_base_workflow_attributes(self):
        # Correct number of actions
        self.assertEqual(len(self.testWorkflow.actions), 1)

        # Asserts workflow entry point
        self.assertTrue(self.testWorkflow.actions[self.workflow_uid])
        action = self.testWorkflow.actions[self.workflow_uid]

        # Verify attributes
        self.assertEqual(action.name, 'start')
        self.assertEqual(action.app_name, 'HelloWorldBounded')
        self.assertEqual(action.action_name, 'repeatBackToMe')

    def test_workflow_branches(self):
        branch = list(self.testWorkflow.branches.values())[0]
        self.assertEqual(len(branch), 1)

        branch = branch[0]
        self.assertTrue(branch.conditions)

    def test_workflow_branch_conditions(self):
        conditions = list(self.testWorkflow.branches.values())[0][0].conditions

        # Verify conditions exist
        self.assertTrue(len(conditions) == 1)

        condition = conditions[0]
        self.assertEqual(condition.action_name, 'regMatch')
        self.assertTrue(condition.transforms)

    def test_workflow_branch_transforms(self):
        transforms = list(self.testWorkflow.branches.values())[0][0].conditions[0].transforms
        self.assertEqual(len(transforms), 1)

        transform = transforms[0]
        self.assertEqual(transform.action_name, 'length')
        self.assertEqual(transform.arguments, {})

    def test_load_workflow_invalid_app(self):
        original_workflows = self.c.get_all_workflows()
        self.c.load_playbook(
            resource='{}invalidAppWorkflow.playbook'.format(config.test_invalid_workflows_path))
        self.assertListEqual(self.c.get_all_workflows(), original_workflows)

    def test_load_workflow_invalid_action(self):
        original_workflows = self.c.get_all_workflows()
        self.c.load_playbook(
            resource='{}invalidActionWorkflow.playbook'.format(config.test_invalid_workflows_path))
        self.assertListEqual(self.c.get_all_workflows(), original_workflows)

    def test_load_workflow_invalid_input(self):
        original_workflows = self.c.get_all_workflows()
        self.c.load_playbook(
            resource='{}invalidInputWorkflow.playbook'.format(config.test_invalid_workflows_path))
        self.assertListEqual(self.c.get_all_workflows(), original_workflows)

    def test_load_workflow_too_many_inputs(self):
        original_workflows = self.c.get_all_workflows()
        self.c.load_playbook(
            resource='{}tooManyActionInputsWorkflow.playbook'.format(config.test_invalid_workflows_path))
        self.assertListEqual(self.c.get_all_workflows(), original_workflows)
