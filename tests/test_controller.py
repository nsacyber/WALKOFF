import unittest

import apps
import core.config.config
from core import helpers
from core.controller import Controller
from tests import config


class TestController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(config.test_apps_path)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.conditions = helpers.import_all_conditions('tests.util.conditionstransforms')
        core.config.config.transforms = helpers.import_all_transforms('tests.util.conditionstransforms')
        core.config.config.load_condition_transform_apis(path=config.function_api_path)

    def setUp(self):
        self.controller = Controller()

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def test_create_controller(self):
        self.assertEqual(self.controller.uid, "controller")

    # def test_load_workflow_from_file(self):
    #     path = '{0}{1}.playbook'.format(config.test_workflows_path_with_generated, "test")
    #     playbook_name = "testPlaybook"
    #     workflow_name = "helloWorldWorkflow"
    #     ret = self.controller.load_workflow_from_file(path=path, workflow_name=workflow_name,
    #                                                   playbook_override=playbook_name)
    #     self.assertTrue(ret)
    #
    # def test_load_workflows_from_file(self):
    #     path = config.test_workflows_path + "tieredWorkflow.playbook"
    #     playbook_name = "testPlaybook"
    #     self.controller.load_playbook_from_file(path=path, playbook_override=playbook_name)
    #     key = _WorkflowKey(playbook_name, "parentWorkflow")
    #     self.assertTrue(key in self.controller.workflows)
    #     key = _WorkflowKey(playbook_name, "childWorkflow")
    #     self.assertTrue(key in self.controller.workflows)
    #
    # def test_load_all_workflows_from_directory(self):
    #     path = config.test_workflows_path
    #     workflows = helpers.locate_playbooks_in_directory(path)
    #     keys = []
    #     invalid_workflows = ['invalidActionWorkflow', 'invalidAppWorkflow',
    #                          'tooManyStepInputsWorkflow', 'invalidInputWorkflow']
    #     for workflow in workflows:
    #         for name in helpers.get_workflow_names_from_file(os.path.join(config.test_workflows_path, workflow)):
    #             playbook_name = workflow.split('.')[0]
    #             if playbook_name not in invalid_workflows:
    #                 keys.append(_WorkflowKey(playbook_name, name))
    #     self.controller.load_all_playbooks_from_directory(path=path)
    #     for key in keys:
    #         self.assertTrue(key in self.controller.workflows)
