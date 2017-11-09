import types
import unittest
from os import sep
from os.path import join

import apps
import core.config.paths
from core.config.config import initialize
from core.helpers import *
from tests.config import test_workflows_path, test_apps_path, function_api_path
from tests.util.assertwrappers import orderless_list_compare


class TestHelperFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.conditions = import_all_conditions('tests.util.conditionstransforms')
        core.config.config.transforms = import_all_transforms('tests.util.conditionstransforms')
        core.config.config.load_condition_transform_apis(path=function_api_path)

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

    def test_import_and_find_tags(self):
        import tests.util.conditionstransforms
        from tests.util.conditionstransforms import sub1, mod1
        from tests.util.conditionstransforms.sub1 import mod2
        filter_tags = import_and_find_tags('tests.util.conditionstransforms', 'transform')
        expected_filters = {'top_level_filter': tests.util.conditionstransforms.top_level_filter,
                            'filter1': tests.util.conditionstransforms.filter1,
                            'length': tests.util.conditionstransforms.length,
                            'json_select': tests.util.conditionstransforms.json_select,
                            'mod1.filter1': tests.util.conditionstransforms.mod1.filter1,
                            'mod1.filter2': tests.util.conditionstransforms.mod1.filter2,
                            'sub1.sub1_top_filter': tests.util.conditionstransforms.sub1.sub1_top_filter,
                            'sub1.mod2.filter1': tests.util.conditionstransforms.sub1.mod2.filter1,
                            'sub1.mod2.complex_filter': tests.util.conditionstransforms.sub1.mod2.complex_filter,
                            'sub1.mod2.filter3': tests.util.conditionstransforms.sub1.mod2.filter3}
        flag_tags = import_and_find_tags('tests.util.conditionstransforms', 'condition')
        expected_flags = {'top_level_flag': tests.util.conditionstransforms.top_level_flag,
                          'regMatch': tests.util.conditionstransforms.regMatch,
                          'count': tests.util.conditionstransforms.count,
                          'mod1.flag1': tests.util.conditionstransforms.mod1.flag1,
                          'mod1.flag2': tests.util.conditionstransforms.mod1.flag2,
                          'sub1.sub1_top_flag': tests.util.conditionstransforms.sub1.sub1_top_flag,
                          'sub1.mod2.flag1': tests.util.conditionstransforms.sub1.mod2.flag1,
                          'sub1.mod2.flag2': tests.util.conditionstransforms.sub1.mod2.flag2}
        self.assertDictEqual(filter_tags, expected_filters)
        self.assertDictEqual(flag_tags, expected_flags)

    def test_import_all_conditions(self):
        self.assertDictEqual(import_all_conditions('tests.util.conditionstransforms'),
                             import_and_find_tags('tests.util.conditionstransforms', 'condition'))

    def test_import_all_transforms(self):
        self.assertDictEqual(import_all_transforms('tests.util.conditionstransforms'),
                             import_and_find_tags('tests.util.conditionstransforms', 'transform'))

    def test_get_app_action_api_valid(self):
        api = get_app_action_api('HelloWorld', 'pause')
        expected = ('main.Main.pause',
                    [{'required': True,
                      'type': 'number',
                      'name': 'seconds',
                      'description': 'Seconds to pause'}])
        self.assertEqual(len(api), 2)
        self.assertEqual(api[0], expected[0])
        self.assertEqual(len(api[1]), 1)
        self.assertDictEqual(api[1][0], expected[1][0])

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

    def test_get_flag_api_valid(self):
        api = get_condition_api('regMatch')
        expected = (
            [{'required': True, 'type': 'string', 'name': 'regex', 'description': 'The regular expression to match'}],
            {'required': True, 'type': 'string', 'name': 'value', 'description': 'The input value'}
        )
        self.assert_params_tuple_equal(api, expected)

    def test_get_flag_api_invalid(self):
        with self.assertRaises(UnknownCondition):
            get_condition_api('invalid')

    def test_get_filter_api_valid(self):
        api = get_transform_api('length')
        expected = ([], {'required': True, 'type': 'string', 'name': 'value', 'description': 'The input collection'})

        self.assert_params_tuple_equal(api, expected)

    def test_get_filter_api_invalid(self):
        with self.assertRaises(UnknownTransform):
            get_transform_api('invalid')

    def test_get_flag_valid(self):
        from tests.util.conditionstransforms import count
        self.assertEqual(get_condition('count'), count)

    def test_get_flag_invalid(self):
        with self.assertRaises(UnknownCondition):
            get_condition('invalid')

    def test_get_filter_valid(self):
        from tests.util.conditionstransforms import length
        self.assertEqual(get_transform('length'), length)

    def test_get_filter_invalid(self):
        with self.assertRaises(UnknownTransform):
            get_transform('invalid')

    def test_dereference_step_routing(self):
        inputs = {'a': 1, 'b': '@step1', 'c': '@step2', 'd': 'test'}
        accumulator = {'step1': '2', 'step2': 3}
        output = {'a': 1, 'b': '2', 'c': 3, 'd': 'test'}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_extra_steps(self):
        inputs = {'a': 1, 'b': '@step1', 'c': '@step2', 'd': 'test'}
        accumulator = {'step1': '2', 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': 3, 'd': 'test'}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_no_referenced(self):
        inputs = {'a': 1, 'b': '2', 'c': 3, 'd': 'test'}
        accumulator = {'step1': '2', 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': 3, 'd': 'test'}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_step_not_found(self):
        inputs = {'a': 1, 'b': '@step2', 'c': '@invalid', 'd': 'test'}
        accumulator = {'step1': '2', 'step2': 3, 'step3': 5}
        with self.assertRaises(InvalidArgument):
            dereference_step_routing(inputs, accumulator, 'message')

    def test_dereference_step_routing_with_nested_inputs(self):
        inputs = {'a': 1, 'b': '2', 'c': '@step1', 'd': {'e': 3, 'f': '@step2'}}
        accumulator = {'step1': '2', 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': '2', 'd': {'e': 3, 'f': 3}}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_with_ref_to_array(self):
        inputs = {'a': 1, 'b': '2', 'c': '@step1', 'd': {'e': 3, 'f': '@step2'}}
        accumulator = {'step1': [1, 2, 3], 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': [1, 2, 3], 'd': {'e': 3, 'f': 3}}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_with_arrays_of_refs(self):
        inputs = {'a': 1, 'b': '2', 'c': ['@step1', '@step2', '@step3'], 'd': {'e': 3, 'f': '@step2'}}
        accumulator = {'step1': 1, 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': [1, 3, 5], 'd': {'e': 3, 'f': 3}}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_with_arrays_of_objects(self):
        inputs = {'a': 1, 'b': '2', 'c': [{'a': '@step1', 'b': '@step2'}, {'a': 10, 'b': '@step3'}],
                  'd': {'e': 3, 'f': '@step2'}}
        accumulator = {'step1': 1, 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': [{'a': 1, 'b': 3}, {'a': 10, 'b': 5}], 'd': {'e': 3, 'f': 3}}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

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
