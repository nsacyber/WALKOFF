import unittest

import apps
import core.config.config
from core import controller
from tests import config
from tests.config import test_apps_path


class TestLoadWorkflow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)

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

        # Correct number of steps
        self.assertEqual(len(self.testWorkflow.steps), 1)

        # Asserts workflow entry point
        self.assertTrue(self.testWorkflow.steps[self.workflow_uid])
        step = self.testWorkflow.steps[self.workflow_uid]

        # Verify attributes
        self.assertEqual(step.name, 'start')
        self.assertEqual(step.app, 'HelloWorld')
        self.assertEqual(step.action, 'repeatBackToMe')
        self.assertIsNone(step.device)

    def test_workflow_next_steps(self):
        next_step = list(self.testWorkflow.next_steps.values())[0]
        self.assertEqual(len(next_step), 1)

        next_step = next_step[0]
        self.assertTrue(next_step.conditions)

    def test_workflow_next_step_conditions(self):
        conditions = list(self.testWorkflow.next_steps.values())[0][0].conditions

        # Verify conditions exist
        self.assertTrue(len(conditions) == 1)

        condition = conditions[0]
        self.assertEqual(condition.action, 'regMatch')
        self.assertTrue(condition.transforms)

    def test_workflow_next_step_transforms(self):
        transforms = list(self.testWorkflow.next_steps.values())[0][0].conditions[0].transforms
        self.assertEqual(len(transforms), 1)

        transform = transforms[0]
        self.assertEqual(transform.action, 'length')
        self.assertEqual(transform.args, {})

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
            resource='{}tooManyStepInputsWorkflow.playbook'.format(config.test_invalid_workflows_path))
        self.assertListEqual(self.c.get_all_workflows(), original_workflows)
