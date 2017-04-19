import unittest
from core.helpers import *
import types
import sys
from os.path import join
from os import sep
from core.instance import Instance
from tests.config import test_workflows_path, test_apps_path
import core.config.paths
from tests.util.assertwrappers import orderless_list_compare

from server import flaskserver as server


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

    def test_import_py_file(self):
        module_name = 'tests.apps.HelloWorld'
        module = import_py_file(module_name, os.path.join(core.config.paths.apps_path, 'HelloWorld', 'main.py'))
        self.assertIsInstance(module, types.ModuleType)
        self.assertEqual(module.__name__, module_name)
        self.assertIn(module_name, sys.modules)
        self.assertEqual(sys.modules[module_name], module)

    def test_import_py_file_invalid(self):
        error_type = IOError if sys.version_info[0] == 2 else OSError
        with self.assertRaises(error_type):
            import_py_file('some.module.name', os.path.join(core.config.paths.apps_path, 'InvalidAppName', 'main.py'))

    def test_import_app_main(self):
        module_name = 'tests.apps.HelloWorld.main'
        module = import_app_main('HelloWorld')
        self.assertIsInstance(module, types.ModuleType)
        self.assertEqual(module.__name__, module_name)
        self.assertIn(module_name, sys.modules)
        self.assertEqual(sys.modules[module_name], module)

    def test_import_app_main_invalid_app(self):
        self.assertIsNone(import_app_main('InvalidAppName'))

    def test_construct_module_name_from_path(self):
        input_output = {join('.', 'aaa', 'bbb', 'ccc'): 'aaa.bbb.ccc',
                        join('aaa', 'bbb', 'ccc'): 'aaa.bbb.ccc',
                        join('aaa', '..', 'bbb', 'ccc'): 'aaa.bbb.ccc',
                        '{0}{1}'.format(join('aaa', 'bbb', 'ccc'), sep): 'aaa.bbb.ccc'}
        for input_path, expected_output in input_output.items():
            self.assertEqual(construct_module_name_from_path(input_path), expected_output)

    def test_import_submodules(self):
        from tests import testpkg
        base_name = 'tests.testpkg'
        results = import_submodules(testpkg)
        expected_names = ['{0}.{1}'.format(base_name, module_name) for module_name in ['a', 'b', 'subpkg']]
        self.assertEqual(len(results.keys()), len(expected_names))
        for name in expected_names:
            self.assertIn(name, results.keys())
            self.assertIn(name, sys.modules.keys())

    def test_import_submodules_recursive(self):
        from tests import testpkg
        base_name = 'tests.testpkg'
        results = import_submodules(testpkg, recursive=True)
        expected_names = ['{0}.{1}'.format(base_name, module_name)
                          for module_name in ['a', 'b', 'subpkg', 'subpkg.c', 'subpkg.d']]
        self.assertEqual(len(results.keys()), len(expected_names))
        for name in expected_names:
            self.assertIn(name, results.keys())
            self.assertIn(name, sys.modules.keys())
