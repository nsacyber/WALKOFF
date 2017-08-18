import unittest
from core import controller
from core.config.config import initialize
from tests import config
from core.controller import _WorkflowKey
from core.helpers import import_all_apps, import_all_filters, import_all_flags
from tests.config import test_apps_path, function_api_path
import core.config.config


class TestLoadWorkflow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import_all_apps(path=test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def setUp(self):
        self.c = controller.Controller(workflows_path=config.test_workflows_path)
        self.c.load_workflows_from_file(path=config.test_workflows_path + 'basicWorkflowTest.playbook')
        self.workflow_name = _WorkflowKey('basicWorkflowTest', 'helloWorldWorkflow')
        self.testWorkflow = self.c.workflows[self.workflow_name]

    def test_workflow_loaded(self):
        # Tests that helloWorldWorkflow exists
        self.assertIn(self.workflow_name, self.c.workflows)

    def test_base_workflow_attributes(self):

        # Correct number of steps
        self.assertEqual(len(self.testWorkflow.steps), 1)

        # Asserts workflow entry point
        self.assertTrue(self.testWorkflow.steps['start'])
        step = self.testWorkflow.steps['start']

        # Verify attributes
        self.assertEqual(step.name, 'start')
        self.assertEqual(step.app, 'HelloWorld')
        self.assertEqual(step.action, 'repeatBackToMe')
        self.assertEqual(step.device, 'hwTest')

    def test_workflow_next_steps(self):
        next_step = self.testWorkflow.steps['start'].conditionals
        self.assertEqual(len(next_step), 1)

        next_step = next_step[0]
        self.assertEqual(next_step.name, '1')
        self.assertTrue(next_step.flags)

    def test_workflow_next_step_flags(self):
        flags = self.testWorkflow.steps['start'].conditionals[0].flags

        # Verify flags exist
        self.assertTrue(len(flags) == 1)

        flag = flags[0]
        self.assertEqual(flag.action, 'regMatch')
        # self.assertDictEqual({'regex': {'key': 'regex', 'type': 'regex', 'value': '(.*)'}}, flag.args)
        self.assertTrue(flag.filters)

    def test_workflow_next_step_filters(self):
        filters = self.testWorkflow.steps['start'].conditionals[0].flags[0].filters
        self.assertEqual(len(filters), 1)

        filter_element = filters[0]
        self.assertEqual(filter_element.action, 'length')
        self.assertEqual(filter_element.args, {})

    def test_load_workflow_invalid_app(self):
        original_workflows = self.c.get_all_workflows()
        self.c.load_workflows_from_file(
            path='{}invalidAppWorkflow.playbook'.format(config.test_invalid_workflows_path))
        self.assertDictEqual(self.c.get_all_workflows(), original_workflows)

    def test_load_workflow_invalid_action(self):
        original_workflows = self.c.get_all_workflows()
        self.c.load_workflows_from_file(
            path='{}invalidActionWorkflow.playbook'.format(config.test_invalid_workflows_path))
        self.assertDictEqual(self.c.get_all_workflows(), original_workflows)

    def test_load_workflow_invalid_input(self):
        original_workflows = self.c.get_all_workflows()
        self.c.load_workflows_from_file(
            path='{}invalidInputWorkflow.playbook'.format(config.test_invalid_workflows_path))
        self.assertDictEqual(self.c.get_all_workflows(), original_workflows)

    def test_load_workflow_too_many_inputs(self):
        original_workflows = self.c.get_all_workflows()
        self.c.load_workflows_from_file(
            path='{}tooManyStepInputsWorkflow.playbook'.format(config.test_invalid_workflows_path))
        self.assertDictEqual(self.c.get_all_workflows(), original_workflows)