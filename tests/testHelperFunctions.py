import unittest
from core.helpers import *

from core.instance import Instance
from tests.config import test_workflows_path, test_apps_path
import core.config.paths
from tests.util.assertwrappers import orderless_list_compare

from server import flaskServer as server

class TestHelperFunctions(unittest.TestCase):
    def setUp(self):
        self.original_apps_path = core.config.paths.apps_path
        core.config.paths.apps_path = test_apps_path

    def tearDown(self):
        core.config.paths.apps_path = self.original_apps_path

    def test_load_app_function(self):

        app = 'HelloWorld'
        with server.running_context.flask_app.app_context():
            instance = Instance.create(app, 'default_device_name')
        existing_actions = {'helloWorld': instance().helloWorld,
                            'repeatBackToMe': instance().repeatBackToMe,
                            'returnPlusOne': instance().returnPlusOne}
        for action, function in existing_actions.items():
            self.assertEqual(load_app_function(instance(), action), function)

    def test_load_app_function_invalid_function(self):
        with server.running_context.flask_app.app_context():
            instance = Instance.create('HelloWorld', 'default_device_name')
        self.assertIsNone(load_app_function(instance(), 'JunkFunctionName'))

    def test_locate_workflows(self):
        expected_workflows = ['basicWorkflowTest.workflow',
                              'DailyQuote.workflow',
                              'loopWorkflow.workflow',
                              'multiactionWorkflowTest.workflow',
                              'multistepError.workflow',
                              'simpleDataManipulationWorkflow.workflow',
                              'templatedWorkflowTest.workflow',
                              'testExecutionWorkflow.workflow',
                              'testScheduler.workflow',
                              'tieredWorkflow.workflow']
        received_workflows = locate_workflows_in_directory(test_workflows_path)
        orderless_list_compare(self, received_workflows, expected_workflows)

        self.assertListEqual(locate_workflows_in_directory('.'), [])

    def test_get_workflow_names_from_file(self):
        workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'basicWorkflowTest.workflow'))
        self.assertListEqual(workflows, ['helloWorldWorkflow'])

        workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'tieredWorkflow.workflow'))
        self.assertListEqual(workflows, ['parentWorkflow', 'childWorkflow'])

        workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'junkfileName.workflow'))
        self.assertIsNone(workflows)

    def test_list_apps(self):
        expected_apps = ['HelloWorld']
        orderless_list_compare(self, expected_apps, list_apps())

    def test_construct_workflow_name_key(self):
        input_output = {('',''): '-',
                        ('', 'test_workflow'): '-test_workflow',
                        ('test_playbook', 'test_workflow'): 'test_playbook-test_workflow',
                        ('-test_playbook', 'test_workflow'): 'test_playbook-test_workflow'}
        for (playbook, workflow), expected_result in input_output.items():
            self.assertEqual(construct_workflow_name_key(playbook, workflow), expected_result)

    def test_extract_workflow_name(self):
        wx = construct_workflow_name_key('www', 'xxx')
        xy = construct_workflow_name_key('xxx', 'yyy')
        yz = construct_workflow_name_key('yyy', 'zzz')
        xyyz = construct_workflow_name_key(xy, yz)
        input_output = {(wx, ''): 'xxx',
                        (wx, 'www'): 'xxx',
                        (wx, 'xxx'): 'xxx',
                        (xyyz, ''): '{0}'.format(construct_workflow_name_key('yyy', yz)),
                        (xyyz, 'xxx'): '{0}'.format(construct_workflow_name_key('yyy', yz)),
                        (xyyz, xy): yz}
        for (workflow_key, playbook_name), expected_workflow in input_output.items():
            self.assertEqual(extract_workflow_name(workflow_key, playbook_name=playbook_name), expected_workflow)
