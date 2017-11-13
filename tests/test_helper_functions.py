import types
import unittest
from os import sep
from os.path import join

import apps
import core.config.paths
from core.config.config import initialize
from core.helpers import *
from tests.config import test_workflows_path, test_apps_path
from tests.util.assertwrappers import orderless_list_compare


class TestHelperFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)

    def setUp(self):
        self.original_apps_path = core.config.paths.apps_path
        core.config.paths.apps_path = test_apps_path

    def tearDown(self):
        core.config.paths.apps_path = self.original_apps_path

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    # TODO: Figure out replacement test
    # def test_load_app_function(self):
    #
    #     app = 'HelloWorld'
    #     with server.running_context.flask_app.app_context():
    #         instance = Instance.create(app, 'default_device_name')
    #     existing_actions = {'helloWorld': instance().helloWorld,
    #                         'repeatBackToMe': instance().repeatBackToMe,
    #                         'returnPlusOne': instance().returnPlusOne}
    #     for action, function in existing_actions.items():
    #         self.assertEqual(load_app_function(instance(), action), function)

    # def test_load_app_function_invalid_function(self):
    #     with server.running_context.flask_app.app_context():
    #         instance = Instance.create('HelloWorld', 'default_device_name')
    #     self.assertIsNone(load_app_function(instance(), 'JunkFunctionName'))

    def test_locate_workflows(self):
        expected_workflows = ['basicWorkflowTest.playbook',
                              'DailyQuote.playbook',
                              'dataflowTest.playbook',
                              'dataflowTestStepNotExecuted.playbook',
                              'loopWorkflow.playbook',
                              'multiactionWorkflowTest.playbook',
                              'pauseWorkflowTest.playbook',
                              'multistepError.playbook',
                              'simpleDataManipulationWorkflow.playbook',
                              'templatedWorkflowTest.playbook',
                              'testExecutionWorkflow.playbook',
                              'testScheduler.playbook']
        received_workflows = locate_playbooks_in_directory(test_workflows_path)
        orderless_list_compare(self, received_workflows, expected_workflows)

        self.assertListEqual(locate_playbooks_in_directory('.'), [])

    def test_get_workflow_names_from_file(self):
        workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'basicWorkflowTest.playbook'))
        self.assertListEqual(workflows, ['helloWorldWorkflow'])

        workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'junkfileName.playbook'))
        self.assertListEqual(workflows, [])

    def test_list_apps(self):
        expected_apps = ['HelloWorld', 'DailyQuote']
        orderless_list_compare(self, expected_apps, list_apps())

    def test_list_widgets(self):
        orderless_list_compare(self, list_widgets('HelloWorld'), ['testWidget', 'testWidget2'])
        self.assertListEqual(list_widgets('JunkApp'), [])

    def test_import_py_file(self):
        module_name = 'tests.testapps.HelloWorld'
        imported_module = import_py_file(module_name,
                                         os.path.join(core.config.paths.apps_path, 'HelloWorld', 'main.py'))
        self.assertIsInstance(imported_module, types.ModuleType)
        self.assertEqual(imported_module.__name__, module_name)
        self.assertIn(module_name, sys.modules)
        self.assertEqual(sys.modules[module_name], imported_module)

    def test_import_py_file_invalid(self):
        error_type = IOError if sys.version_info[0] == 2 else OSError
        with self.assertRaises(error_type):
            import_py_file('some.module.name', os.path.join(core.config.paths.apps_path, 'InvalidAppName', 'main.py'))

    def test_import_app_main(self):
        module_name = 'tests.testapps.HelloWorld.main'
        imported_module = import_app_main('HelloWorld')
        self.assertIsInstance(imported_module, types.ModuleType)
        self.assertEqual(imported_module.__name__, module_name)
        self.assertIn(module_name, sys.modules)
        self.assertEqual(sys.modules[module_name], imported_module)

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

    def test_format_db_path(self):
        self.assertEqual(format_db_path('sqlite', 'aa.db'), 'sqlite:///aa.db')
        self.assertEqual(format_db_path('postgresql', 'aa.db'), 'postgresql://aa.db')


    # def test_get_app_action_api_valid(self):
    #     api = get_app_action_api('HelloWorld', 'pause')
    #     expected = ('main.Main.pause',
    #                 [{'required': True,
    #                   'type': 'number',
    #                   'name': 'seconds',
    #                   'description': 'Seconds to pause'}])
    #     self.assertEqual(len(api), 2)
    #     self.assertEqual(api[0], expected[0])
    #     self.assertEqual(len(api[1]), 1)
    #     self.assertDictEqual(api[1][0], expected[1][0])

    def test_get_app_action_api_invalid_app(self):
        with self.assertRaises(UnknownApp):
            get_app_action_api('InvalidApp', 'pause')

    def test_get_app_action_api_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            get_app_action_api('HelloWorld', 'invalid')

    def assert_params_tuple_equal(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(len(actual), 2)
        self.assertDictEqual(actual[1], expected[1])
        self.assertEqual(len(actual[0]), len(expected[0]))
        for actual_param in actual[0]:
            self.assertIn(actual_param, expected[0])

    # def test_get_flag_api_valid(self):
    #     api = get_condition_api('HelloWorld', 'regMatch')
    #     expected = ('conditions.regMatch',
    #         [{'required': True, 'type': 'string', 'name': 'regex', 'description': 'The regular expression to match'}],
    #         {'required': True, 'type': 'string', 'name': 'value', 'description': 'The input value'}
    #     )
    #     expected = ('conditions.regMatch',
    #         [{'required': True, 'type': 'string', 'name': 'regex', 'description': 'The regular expression to match'}],
    #         {'required': True, 'type': 'string', 'name': 'value', 'description': 'The input value'})
    #
    #     print(api)
    #     print(len(api))
    #     print(len(expected))
    #     self.assert_params_tuple_equal(api, expected)

    def test_get_flag_api_invalid(self):
        with self.assertRaises(UnknownCondition):
            get_condition_api('HelloWorld', 'invalid')

    # def test_get_filter_api_valid(self):
    #     api = get_transform_api('HelloWorld', 'length')
    #     expected = ([], {'required': True, 'type': 'string', 'name': 'value', 'description': 'The input collection'})
    #
    #     self.assert_params_tuple_equal(api, expected)

    def test_get_filter_api_invalid(self):
        with self.assertRaises(UnknownTransform):
            get_transform_api('HelloWorld', 'invalid')

    def test_get_arg_names_no_args(self):
        def x(): pass

        self.assertListEqual(get_function_arg_names(x), [])

    def test_get_arg_names(self):
        def x(a, b, c): pass

        self.assertListEqual(get_function_arg_names(x), ['a', 'b', 'c'])

    def test_format_exception_message_no_exception_message(self):
        class CustomError(Exception):
            pass

        try:
            raise CustomError
        except CustomError as e:
            self.assertEqual(format_exception_message(e), 'CustomError')

    def test_format_exception_message_with_exception_message(self):
        class CustomError(Exception):
            pass

        try:
            raise CustomError('test')
        except CustomError as e:
            self.assertEqual(format_exception_message(e), 'CustomError: test')
