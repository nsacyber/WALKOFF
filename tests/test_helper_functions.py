import types
import unittest
from os import sep
from os.path import join

import walkoff.appgateway
import walkoff.config
from tests.config import test_apps_path
from tests.util.assertwrappers import orderless_list_compare
from walkoff.helpers import *
from walkoff.server.flaskserver import handle_database_errors, handle_generic_server_error


class TestHelperFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.appgateway.cache_apps(test_apps_path)
        walkoff.config.load_app_apis(apps_path=test_apps_path)

    def setUp(self):
        self.original_apps_path = walkoff.config.Config.APPS_PATH
        walkoff.config.Config.APPS_PATH = test_apps_path

    def tearDown(self):
        walkoff.config.Config.APPS_PATH = self.original_apps_path

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()

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

    # def test_locate_workflows(self):
    #     expected_workflows = ['basicWorkflowTest.playbook',
    #                           'DailyQuote.playbook',
    #                           'dataflowTest.playbook',
    #                           'dataflowTestActionNotExecuted.playbook',
    #                           'loopWorkflow.playbook',
    #                           'multiactionWorkflowTest.playbook',
    #                           'pauseWorkflowTest.playbook',
    #                           'multiactionError.playbook',
    #                           'simpleDataManipulationWorkflow.playbook',
    #                           'templatedWorkflowTest.playbook',
    #                           'testExecutionWorkflow.playbook',
    #                           'testScheduler.playbook']
    #     received_workflows = locate_playbooks_in_directory(test_workflows_path)
    #     orderless_list_compare(self, received_workflows, expected_workflows)
    #
    #     self.assertListEqual(locate_playbooks_in_directory('.'), [])
    #
    # def test_get_workflow_names_from_file(self):
    #     workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'basicWorkflowTest.playbook'))
    #     self.assertListEqual(workflows, ['helloWorldWorkflow'])
    #
    #     workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'junkfileName.playbook'))
    #     self.assertListEqual(workflows, [])

    def test_list_apps(self):
        expected_apps = ['HelloWorld', 'DailyQuote', 'HelloWorldBounded']
        orderless_list_compare(self, expected_apps, list_apps())

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

    def test_get_flag_api_invalid(self):
        with self.assertRaises(UnknownCondition):
            get_condition_api('HelloWorld', 'invalid')

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

    def test_create_sse_event_empty_args(self):
        self.assertEqual(create_sse_event(), '')

    def test_create_sse_event_id_only(self):
        self.assertEqual(create_sse_event(event_id=1), 'id: 1\ndata: ""\n\n')

    def test_create_sse_event_only(self):
        self.assertEqual(create_sse_event(event='some_event'), 'event: some_event\ndata: ""\n\n')

    def test_create_sse_data_only_non_json(self):
        self.assertEqual(create_sse_event(data=42), 'data: 42\n\n')

    def test_create_sse_data_only_json(self):
        data = {'a': [1, 2, 3, 4], 'b': {'c': 'something', 'd': ['1', '2', '3']}}
        self.assertEqual(create_sse_event(data=data), 'data: {}\n\n'.format(json.dumps(data)))

    def test_create_sse_full(self):
        data = {'a': [1, 2, 3, 4], 'b': {'c': 'something', 'd': ['1', '2', '3']}}
        self.assertEqual(create_sse_event(event_id=1, event='something', data=data),
                         'id: 1\nevent: something\ndata: {}\n\n'.format(json.dumps(data)))

    def test_database_connection_error_handler(self):
        from sqlalchemy.exc import SQLAlchemyError
        class DbException(SQLAlchemyError): pass

        response = handle_database_errors(DbException())
        self.assertEqual(response.status_code, 500)
        body = json.loads(response.response[0].decode('utf-8'))
        expected = {
            'type': 'about:blank',
            'status': 500,
            'title': 'A database error occurred.',
            'detail': 'DbException'}
        self.assertDictEqual(body, expected)

    def test_server_error_handler(self):
        class SomeException(Exception): pass

        response = handle_generic_server_error(SomeException())
        self.assertEqual(response.status_code, 500)
        body = json.loads(response.response[0].decode('utf-8'))
        expected = {
            'type': 'about:blank',
            'status': 500,
            'title': 'An error occurred in the server.',
            'detail': 'SomeException'}
        self.assertDictEqual(body, expected)
