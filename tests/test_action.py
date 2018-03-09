import unittest

import tests.config
import tests.config
import walkoff.appgateway
import walkoff.config.config
import walkoff.config.paths
from tests.util import execution_db_help
from walkoff.appgateway.actionresult import ActionResult
from walkoff.appgateway.appinstance import AppInstance
from walkoff.events import WalkoffEvent
from walkoff.executiondb.action import Action
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.condition import Condition
from walkoff.executiondb.conditionalexpression import ConditionalExpression
from walkoff.executiondb.position import Position
from walkoff.helpers import InvalidArgument
from walkoff.helpers import InvalidExecutionElement


class TestAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()
        walkoff.appgateway.cache_apps(tests.config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=tests.config.test_apps_path)

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        execution_db_help.tear_down_execution_db()

    def __compare_init(self, elem, app_name, action_name, name, device_id=None, arguments=None, trigger=None,
                       position=None):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.action_name, action_name)
        self.assertEqual(elem.app_name, app_name)
        self.assertEqual(elem.device_id, device_id)
        if arguments:
            self.assertListEqual(elem.arguments, arguments)
        if trigger:
            self.assertEqual(elem.trigger.operator, trigger.operator)
        if position:
            self.assertEqual(elem.position.x, position.x)
            self.assertEqual(elem.position.y, position.y)
        self.assertIsNone(elem._output)
        self.assertEqual(elem._execution_id, 'default')

    def test_init_default(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld')
        self.__compare_init(action, 'HelloWorld', 'helloWorld', 'helloWorld')

    def test_init_with_name(self):
        action = Action('HelloWorld', 'helloWorld', 'test')
        self.__compare_init(action, 'HelloWorld', 'helloWorld', 'test')

    def test_init_with_position(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld', position=Position(13, 42))
        self.__compare_init(action, 'HelloWorld', 'helloWorld', 'helloWorld', position=Position(13, 42))

    def test_get_execution_id(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld')
        self.assertEqual(action.get_execution_id(), action._execution_id)

    def test_init_app_action_only(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld')
        self.__compare_init(action, 'HelloWorld', 'helloWorld', 'helloWorld')

    def test_init_app_and_action_name_different_than_method_name(self):
        action = Action('HelloWorld', 'Hello World', 'helloWorld')
        self.__compare_init(action, 'HelloWorld', 'Hello World', 'helloWorld')

    def test_init_invalid_app(self):
        with self.assertRaises(InvalidExecutionElement):
            Action('InvalidApp', 'helloWorld', 'helloWorld')

    def test_init_invalid_action(self):
        with self.assertRaises(InvalidExecutionElement):
            Action('HelloWorld', 'invalid', 'helloWorld')

    def test_init_app_action_only_with_device(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld', device_id='test')
        self.__compare_init(action, 'HelloWorld', 'helloWorld', 'helloWorld', device_id='test')

    def test_init_with_arguments_no_conversion(self):
        action = Action('HelloWorld', 'returnPlusOne', 'returnPlusOne', arguments=[Argument('number', value=-5.6)])
        self.__compare_init(action, 'HelloWorld', 'returnPlusOne', 'returnPlusOne',
                            arguments=[Argument('number', value=-5.6)])

    def test_init_with_arguments_with_conversion(self):
        action = Action('HelloWorld', 'returnPlusOne', 'returnPlusOne', arguments=[Argument('number', value='-5.6')])
        self.__compare_init(action, 'HelloWorld', 'returnPlusOne', 'returnPlusOne',
                            arguments=[Argument('number', value='-5.6')])

    def test_init_with_invalid_argument_name(self):
        with self.assertRaises(InvalidExecutionElement):
            Action('HelloWorld', 'returnPlusOne', 'helloWorld', arguments=[Argument('invalid', value='-5.6')])

    def test_init_with_invalid_argument_type(self):
        with self.assertRaises(InvalidExecutionElement):
            Action('HelloWorld', 'returnPlusOne', 'helloWorld', arguments=[Argument('number', value='invalid')])

    def test_init_with_triggers(self):
        trigger = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='(.*)')]),
                        Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='a')])])
        action = Action('HelloWorld', 'helloWorld', 'helloWorld', trigger=trigger)
        self.__compare_init(action, 'HelloWorld', 'helloWorld', 'helloWorld', trigger=trigger)

    def test_execute_no_args(self):
        action = Action(app_name='HelloWorld', action_name='helloWorld', name='helloWorld')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        self.assertEqual(action.execute(instance.instance, {}), ActionResult({'message': 'HELLO WORLD'}, 'Success'))
        self.assertEqual(action._output, ActionResult({'message': 'HELLO WORLD'}, 'Success'))

    def test_execute_return_failure(self):
        action = Action(app_name='HelloWorld', action_name='dummy action', name='helloWorld',
                        arguments=[Argument('status', value=False)])
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = {'started_triggered': False, 'result_triggered': False}

        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, Action):
                self.assertIn('event', kwargs)
                self.assertIn(kwargs['event'], (WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionError))
                if kwargs['event'] == WalkoffEvent.ActionStarted:
                    result['started_triggered'] = True
                else:
                    self.assertIn('data', kwargs)
                    data = kwargs['data']
                    self.assertEqual(data['status'], 'Failure')
                    self.assertEqual(data['result'], False)
                    result['result_triggered'] = True

        WalkoffEvent.CommonWorkflowSignal.connect(callback_is_sent)

        action.execute(instance.instance, {})
        self.assertTrue(result['started_triggered'])
        self.assertTrue(result['result_triggered'])

    def test_execute_default_return_success(self):
        action = Action(app_name='HelloWorld', action_name='dummy action', name='helloWorld',
                        arguments=[Argument('status', value=True), Argument('other', value=True)])
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = {'started_triggered': False, 'result_triggered': False}

        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, Action):
                self.assertIn('event', kwargs)
                self.assertIn(kwargs['event'], (WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionSuccess))
                if kwargs['event'] == WalkoffEvent.ActionStarted:
                    result['started_triggered'] = True
                else:
                    self.assertIn('data', kwargs)
                    data = kwargs['data']
                    self.assertEqual(data['status'], 'Success')
                    self.assertEqual(data['result'], None)
                    result['result_triggered'] = True

        WalkoffEvent.CommonWorkflowSignal.connect(callback_is_sent)

        action.execute(instance.instance, {})

        self.assertTrue(result['started_triggered'])
        self.assertTrue(result['result_triggered'])

    def test_execute_generates_id(self):
        action = Action(app_name='HelloWorld', action_name='helloWorld', name='helloWorld')
        original_execution_id = action.get_execution_id()
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        action.execute(instance.instance, {})
        self.assertNotEqual(action.get_execution_id(), original_execution_id)

    def test_execute_with_args(self):
        action = Action(app_name='HelloWorld', action_name='Add Three', name='helloWorld',
                        arguments=[Argument('num1', value='-5.6'),
                                   Argument('num2', value='4.3'),
                                   Argument('num3', value='10.2')])
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = action.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(action._output, result)

    def test_execute_sends_callbacks(self):
        action = Action(app_name='HelloWorld', action_name='Add Three', name='helloWorld',
                        arguments=[Argument('num1', value='-5.6'),
                                   Argument('num2', value='4.3'),
                                   Argument('num3', value='10.2')])
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        result = {'started_triggered': False, 'result_triggered': False}

        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, Action):
                self.assertIn('event', kwargs)
                self.assertIn(kwargs['event'], (WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionSuccess))
                if kwargs['event'] == WalkoffEvent.ActionStarted:
                    result['started_triggered'] = True
                else:
                    self.assertIn('data', kwargs)
                    data = kwargs['data']
                    self.assertEqual(data['status'], 'Success')
                    self.assertAlmostEqual(data['result'], 8.9)
                    result['result_triggered'] = True

        WalkoffEvent.CommonWorkflowSignal.connect(callback_is_sent)

        action.execute(instance.instance, {})
        self.assertTrue(result['started_triggered'])
        self.assertTrue(result['result_triggered'])

    def test_execute_with_accumulator_with_conversion(self):
        action = Action(app_name='HelloWorld', action_name='Add Three', name='helloWorld',
                        arguments=[Argument('num1', reference='1'),
                                   Argument('num2', reference='action2'),
                                   Argument('num3', value='10.2')])
        accumulator = {'1': '-5.6', 'action2': '4.3'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = action.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(action._output, result)

    def test_execute_with_accumulator_with_extra_actions(self):
        action = Action(app_name='HelloWorld', action_name='Add Three', name='helloWorld',
                        arguments=[Argument('num1', reference='1'),
                                   Argument('num2', reference='action2'),
                                   Argument('num3', value='10.2')])
        accumulator = {'1': '-5.6', 'action2': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = action.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(action._output, result)

    def test_execute_with_accumulator_missing_action(self):
        action = Action(app_name='HelloWorld', action_name='Add Three', name='helloWorld',
                        arguments=[Argument('num1', reference='1'),
                                   Argument('num2', reference='action2'),
                                   Argument('num3', value='10.2')])
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        action.execute(instance.instance, accumulator)

    def test_execute_with_accumulator_missing_action_callbacks(self):
        action = Action(app_name='HelloWorld', action_name='Add Three', name='helloWorld',
                        arguments=[Argument('num1', reference='1'),
                                   Argument('num2', reference='action2'),
                                   Argument('num3', value='10.2')])
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        result = {'started_triggered': False, 'result_triggered': False}

        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, Action):
                self.assertIn('event', kwargs)
                self.assertIn(kwargs['event'], (WalkoffEvent.ActionStarted, WalkoffEvent.ActionArgumentsInvalid))
                if kwargs['event'] == WalkoffEvent.ActionStarted:
                    result['started_triggered'] = True
                else:
                    result['result_triggered'] = True

        WalkoffEvent.CommonWorkflowSignal.connect(callback_is_sent)
        action.execute(instance.instance, accumulator)

        self.assertTrue(result['started_triggered'])
        self.assertTrue(result['result_triggered'])

    def test_execute_with_complex_args(self):
        action = Action(app_name='HelloWorld', action_name='Json Sample', name='helloWorld',
                        arguments=[
                            Argument('json_in', value={'a': '-5.6', 'b': {'a': '4.3', 'b': 5.3}, 'c': ['1', '2', '3'],
                                                       'd': [{'a': '', 'b': 3}, {'a': '', 'b': -1.5},
                                                             {'a': '', 'b': -0.5}]})])
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = action.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 11.0)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(action._output, result)

    def test_execute_action_which_raises_exception(self):
        action = Action(app_name='HelloWorld', action_name='Buggy', name='helloWorld')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        action.execute(instance.instance, {})
        self.assertIsNotNone(action.get_output())

    def test_execute_action_which_raises_exception_sends_callbacks(self):
        action = Action(app_name='HelloWorld', action_name='Buggy', name='helloWorld')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        result = {'started_triggered': False, 'result_triggered': False}

        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, Action):
                self.assertIn('event', kwargs)
                self.assertIn(kwargs['event'], (WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionError))
                if kwargs['event'] == WalkoffEvent.ActionStarted:
                    result['started_triggered'] = True
                elif kwargs['event'] == WalkoffEvent.ActionExecutionError:
                    result['result_triggered'] = True

        WalkoffEvent.CommonWorkflowSignal.connect(callback_is_sent)

        action.execute(instance.instance, {})

        self.assertTrue(result['started_triggered'])
        self.assertTrue(result['result_triggered'])

    def test_execute_global_action(self):
        action = Action(app_name='HelloWorld', action_name='global2', name='helloWorld',
                        arguments=[Argument('arg1', value='something')])
        instance = AppInstance.create(app_name='HelloWorld', device_name='')
        result = action.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 'something')
        self.assertEqual(result.status, 'Success')
        self.assertEqual(action._output, result)

    def test_set_args_valid(self):
        action = Action(app_name='HelloWorld', action_name='Add Three', name='helloWorld',
                        arguments=[Argument('num1', value='-5.6'),
                                   Argument('num2', value='4.3'),
                                   Argument('num3', value='10.2')])
        arguments = [Argument('num1', value='-5.62'), Argument('num2', value='5'), Argument('num3', value='42.42')]
        action.set_arguments(arguments)

        self.assertEqual(len(action.arguments), len(arguments))
        for arg in action.arguments:
            self.assertIn(arg, arguments)

    def test_set_args_invalid_name(self):
        action = Action(app_name='HelloWorld', action_name='Add Three', name='helloWorld',
                        arguments=[Argument('num1', value='-5.6'),
                                   Argument('num2', value='4.3'),
                                   Argument('num3', value='10.2')])
        with self.assertRaises(InvalidArgument):
            action.set_arguments(
                [Argument('num1', value='-5.62'), Argument('invalid', value='5'), Argument('num3', value='42.42')])

    def test_set_args_invalid_format(self):
        action = Action(app_name='HelloWorld', action_name='Add Three', name='helloWorld',
                        arguments=[Argument('num1', value='-5.6'),
                                   Argument('num2', value='4.3'),
                                   Argument('num3', value='10.2')])
        with self.assertRaises(InvalidArgument):
            action.set_arguments(
                [Argument('num1', value='-5.62'), Argument('num2', value='5'), Argument('num3', value='invalid')])

    def test_execute_with_triggers(self):
        trigger = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])])
        action = Action(app_name='HelloWorld', action_name='helloWorld', name='helloWorld', trigger=trigger)
        ret = action.execute_trigger({"data_in": {"data": 'aaa'}}, {})

        self.assertTrue(ret)

    def test_execute_multiple_triggers(self):
        trigger = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])])
        action = Action(app_name='HelloWorld', action_name='helloWorld', name='helloWorld', trigger=trigger)
        AppInstance.create(app_name='HelloWorld', device_name='device1')
        self.assertFalse(action.execute_trigger({"data_in": {"data": 'a'}}, {}))
        self.assertTrue(action.execute_trigger({"data_in": {"data": 'aaa'}}, {}))
