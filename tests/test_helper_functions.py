import unittest

import walkoff.appgateway
import walkoff.config
from tests.util import initialize_test_config
from tests.util.assertwrappers import orderless_list_compare
from walkoff.appgateway.apiutil import get_app_action_api, get_condition_api, get_transform_api, UnknownApp, \
    UnknownAppAction, UnknownCondition, UnknownTransform
from walkoff.helpers import *
from walkoff.server.blueprints.root import handle_database_errors, handle_generic_server_error
from walkoff.server.app import create_app


class TestHelperFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        cls.app = create_app()
        cls.app.testing = True
        cls.context = cls.app.test_request_context()
        cls.context.push()

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
        orderless_list_compare(self, expected_apps, list_apps(walkoff.config.Config.APPS_PATH))

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

    def test_strip_device_ids(self):
        playbook = {
            'name': 'some_playbook',
            'workflows': [
                {'name': 'wf1',
                 'actions': [{'name': 'action1'}, {'name': 'action2', 'device_id': 42}]},
                {'name': 'wf2',
                 'actions': [{'name': 'action1', 'device_id': 13}, {'name': 'some_action', 'device_id': 21}]}
            ]}
        expected = {
            'name': 'some_playbook',
            'workflows': [
                {'name': 'wf1',
                 'actions': [{'name': 'action1'}, {'name': 'action2'}]},
                {'name': 'wf2',
                 'actions': [{'name': 'action1'}, {'name': 'some_action'}]}
            ]}
        strip_device_ids(playbook)
        self.assertDictEqual(playbook, expected)

    def test_strip_argument_ids_from_element(self):
        element_with_arguments = {
            'a': 'string1',
            'b': {'red': 'blue', 'green': 'red'},
            'arguments': [
                {
                    'id': 4,
                    'value': 32
                },
                {
                    'id': 12,
                    'reference': 'abc-123-456gh'
                }
            ]
        }
        expected = {
            'a': 'string1',
            'b': {'red': 'blue', 'green': 'red'},
            'arguments': [
                {
                    'value': 32
                },
                {
                    'reference': 'abc-123-456gh'
                }
            ]
        }
        strip_argument_ids_from_element(element_with_arguments)
        self.assertDictEqual(element_with_arguments, expected)
        element_no_arguments = {
            'a': 'string1',
            'b': {'red': 'blue', 'green': 'red'},
        }
        expected = {
            'a': 'string1',
            'b': {'red': 'blue', 'green': 'red'},
        }
        strip_argument_ids_from_element(element_no_arguments)
        self.assertDictEqual(element_no_arguments, expected)

    def test_strip_argument_ids_from_conditional(self):
        conditional = {
            'operator': 'and',
            'is_negated': True,
            'conditions': [
                {
                    'app_name': 'ArgleBargle',
                    'action_name': 'flim flam',
                    'arguments': [
                        {
                            'id': 42,
                            'value': 'foobar'
                        },
                        {
                            'id': 12,
                            'value': 'wizbang'
                        }
                    ],
                    'transforms': [
                        {
                            'app_name': 'transmorgifier',
                            'action': 'transmorgify',
                            'arguments': [
                                {
                                    'id': 23,
                                    'value': 'zapzorp'
                                }
                            ]
                        }
                    ]
                },
                {
                    'app_name': 'Wombology',
                    'action_name': 'wombo',
                    'arguments': [
                        {
                            'id': 13,
                            'value': 'gee'
                        },
                        {
                            'id': 12,
                            'reference': 'abc-def-ghi123'
                        }
                    ]
                }
            ],
            'child_expressions': [
                {
                    'operator': 'and',
                    'is_negated': True,
                    'conditions': [
                        {
                            'app_name': 'ArgleBargle',
                            'action_name': 'flim flam',
                            'arguments': [
                                {
                                    'id': 42,
                                    'value': 'foobar'
                                },
                                {
                                    'id': 12,
                                    'value': 'wizbang'
                                }
                            ]
                        },
                        {
                            'app_name': 'Wombology',
                            'action_name': 'wombo',
                            'arguments': [
                                {
                                    'id': 13,
                                    'value': 'gee'
                                },
                                {
                                    'id': 12,
                                    'reference': 'abc-def-ghi123'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        expected = {
            'operator': 'and',
            'is_negated': True,
            'conditions': [
                {
                    'app_name': 'ArgleBargle',
                    'action_name': 'flim flam',
                    'arguments': [
                        {
                            'value': 'foobar'
                        },
                        {
                            'value': 'wizbang'
                        }
                    ],
                    'transforms': [
                        {
                            'app_name': 'transmorgifier',
                            'action': 'transmorgify',
                            'arguments': [
                                {
                                    'value': 'zapzorp'
                                }
                            ]
                        }
                    ]
                },
                {
                    'app_name': 'Wombology',
                    'action_name': 'wombo',
                    'arguments': [
                        {
                            'value': 'gee'
                        },
                        {
                            'reference': 'abc-def-ghi123'
                        }
                    ]
                }
            ],
            'child_expressions': [
                {
                    'operator': 'and',
                    'is_negated': True,
                    'conditions': [
                        {
                            'app_name': 'ArgleBargle',
                            'action_name': 'flim flam',
                            'arguments': [
                                {
                                    'value': 'foobar'
                                },
                                {
                                    'value': 'wizbang'
                                }
                            ]
                        },
                        {
                            'app_name': 'Wombology',
                            'action_name': 'wombo',
                            'arguments': [
                                {
                                    'value': 'gee'
                                },
                                {
                                    'reference': 'abc-def-ghi123'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        strip_argument_ids_from_conditional(conditional)
        self.assertDictEqual(conditional, expected)