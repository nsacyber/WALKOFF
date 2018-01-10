import unittest

import walkoff.appgateway
import walkoff.config.config
import walkoff.config.paths
from walkoff import initialize_databases
from walkoff.appgateway.appinstance import AppInstance
from walkoff.coredb.argument import Argument
from walkoff.core.actionresult import ActionResult
from walkoff.events import WalkoffEvent
from walkoff.coredb.action import Action
from walkoff.coredb.condition import Condition
from walkoff.helpers import UnknownApp, UnknownAppAction, InvalidArgument
import tests.config


class TestAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.config.paths.db_path = tests.config.test_db_path
        walkoff.config.paths.case_db_path = tests.config.test_case_db_path
        walkoff.config.paths.device_db_path = tests.config.test_device_db_path
        initialize_databases()
        walkoff.appgateway.cache_apps(tests.config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=tests.config.test_apps_path)

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()

    def __compare_init(self, elem, app_name, action_name, name=None, device_id=None, arguments=None, triggers=None,
                       x_coordinate=None, y_coordinate=None, templated=False, raw_representation=None):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.action_name, action_name)
        self.assertEqual(elem.app_name, app_name)
        self.assertEqual(elem.device_id, device_id)
        if arguments:
            self.assertListEqual(elem.arguments, arguments)
        if triggers:
            self.assertEqual(len(elem.triggers), len(triggers))
            self.assertSetEqual({trigger.action_name for trigger in elem.triggers}, set(triggers))
        self.assertEqual(elem.x_coordinate, x_coordinate)
        self.assertEqual(elem.y_coordinate, y_coordinate)
        if templated:
            self.assertTrue(elem.templated)
            self.assertDictEqual(elem._raw_representation, raw_representation)
        else:
            self.assertFalse(elem.templated)
            self.assertDictEqual(elem._raw_representation, {})
        self.assertIsNone(elem._output)
        self.assertEqual(elem._execution_uid, 'default')

    def test_init_default(self):
        action = Action('HelloWorld', 'helloWorld')
        self.__compare_init(action, 'HelloWorld', 'helloWorld')

    def test_init_with_name(self):
        action = Action('HelloWorld', 'helloWorld', name='test')
        self.__compare_init(action, 'HelloWorld', 'helloWorld', 'test')

    def test_init_with_position(self):
        action = Action('HelloWorld', 'helloWorld', x_coordinate=13, y_coordinate=42)
        self.__compare_init(action, 'HelloWorld', 'helloWorld', x_coordinate=13, y_coordinate=42)

    def test_init_templated(self):
        action = Action('HelloWorld', 'helloWorld', templated=True, raw_representation={'a': 42})
        self.__compare_init(action, 'HelloWorld', 'helloWorld', templated=True, raw_representation={'a': 42})

    def test_get_execution_uid(self):
        action = Action('HelloWorld', 'helloWorld')
        self.assertEqual(action.get_execution_uid(), action._execution_uid)

    def test_init_app_action_only(self):
        action = Action('HelloWorld', 'helloWorld')
        self.__compare_init(action, 'HelloWorld', 'helloWorld')

    def test_init_app_and_action_name_different_than_method_name(self):
        action = Action(app_name='HelloWorld', action_name='Hello World')
        self.__compare_init(action, 'HelloWorld', 'Hello World')

    def test_init_invalid_app(self):
        with self.assertRaises(UnknownApp):
            Action('InvalidApp', 'helloWorld')

    def test_init_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            Action(app_name='HelloWorld', action_name='invalid')

    def test_init_app_action_only_with_device(self):
        action = Action('HelloWorld', 'helloWorld', device_id='test')
        self.__compare_init(action, 'HelloWorld', 'helloWorld', device_id='test')

    def test_init_with_arguments_no_conversion(self):
        action = Action('HelloWorld', 'returnPlusOne', arguments=[Argument('number', value=-5.6)])
        self.__compare_init(action, 'HelloWorld', 'returnPlusOne',
                            arguments=[Argument('number', value=-5.6)])

    def test_init_with_arguments_with_conversion(self):
        action = Action('HelloWorld', 'returnPlusOne', arguments=[Argument('number', value='-5.6')])
        self.__compare_init(action, 'HelloWorld', 'returnPlusOne',
                            arguments=[Argument('number', value='-5.6')])

    def test_init_with_invalid_argument_name(self):
        with self.assertRaises(InvalidArgument):
            Action('HelloWorld', 'returnPlusOne', arguments=[Argument('invalid', value='-5.6')])

    def test_init_with_invalid_argument_type(self):
        with self.assertRaises(InvalidArgument):
            Action('HelloWorld', 'returnPlusOne', arguments=[Argument('number', value='invalid')])

    def test_init_with_triggers(self):
        triggers = [Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='(.*)')]),
                    Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='a')])]
        action = Action('HelloWorld', 'helloWorld', triggers=triggers)
        self.__compare_init(action, 'HelloWorld', 'helloWorld', triggers=['regMatch', 'regMatch'])

    def test_execute_no_args(self):
        action = Action(app_name='HelloWorld', action_name='helloWorld')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        self.assertEqual(action.execute(instance.instance, {}), ActionResult({'message': 'HELLO WORLD'}, 'Success'))
        self.assertEqual(action._output, ActionResult({'message': 'HELLO WORLD'}, 'Success'))

    def test_execute_return_failure(self):
        action = Action(app_name='HelloWorld', action_name='dummy action',
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
        action = Action(app_name='HelloWorld', action_name='dummy action',
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

    def test_execute_generates_uid(self):
        action = Action(app_name='HelloWorld', action_name='helloWorld')
        original_execution_uid = action.get_execution_uid()
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        action.execute(instance.instance, {})
        self.assertNotEqual(action.get_execution_uid(), original_execution_uid)

    def test_execute_with_args(self):
        action = Action(app_name='HelloWorld', action_name='Add Three',
                        arguments=[Argument('num1', value='-5.6'),
                                   Argument('num2', value='4.3'),
                                   Argument('num3', value='10.2')])
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = action.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(action._output, result)

    def test_execute_sends_callbacks(self):
        action = Action(app_name='HelloWorld', action_name='Add Three',
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
        action = Action(app_name='HelloWorld', action_name='Add Three',
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
        action = Action(app_name='HelloWorld', action_name='Add Three',
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
        action = Action(app_name='HelloWorld', action_name='Add Three',
                        arguments=[Argument('num1', reference='1'),
                                   Argument('num2', reference='action2'),
                                   Argument('num3', value='10.2')])
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        action.execute(instance.instance, accumulator)

    def test_execute_with_accumulator_missing_action_callbacks(self):
        action = Action(app_name='HelloWorld', action_name='Add Three',
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
        action = Action(app_name='HelloWorld', action_name='Json Sample',
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
        action = Action(app_name='HelloWorld', action_name='Buggy')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        action.execute(instance.instance, {})
        self.assertIsNotNone(action.get_output())

    def test_execute_action_which_raises_exception_sends_callbacks(self):
        action = Action(app_name='HelloWorld', action_name='Buggy')
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
        action = Action(app_name='HelloWorld', action_name='global2', arguments=[Argument('arg1', value='something')])
        instance = AppInstance.create(app_name='HelloWorld', device_name='')
        result = action.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 'something')
        self.assertEqual(result.status, 'Success')
        self.assertEqual(action._output, result)

    def test_set_args_valid(self):
        action = Action(app_name='HelloWorld', action_name='Add Three',
                        arguments=[Argument('num1', value='-5.6'),
                                   Argument('num2', value='4.3'),
                                   Argument('num3', value='10.2')])
        arguments = [Argument('num1', value='-5.62'), Argument('num2', value='5'), Argument('num3', value='42.42')]
        action.set_arguments(arguments)

        self.assertEqual(len(action.arguments), len(arguments))
        for arg in action.arguments:
            self.assertIn(arg, arguments)

    def test_set_args_invalid_name(self):
        action = Action(app_name='HelloWorld', action_name='Add Three',
                        arguments=[Argument('num1', value='-5.6'),
                                   Argument('num2', value='4.3'),
                                   Argument('num3', value='10.2')])
        with self.assertRaises(InvalidArgument):
            action.set_arguments(
                [Argument('num1', value='-5.62'), Argument('invalid', value='5'), Argument('num3', value='42.42')])

    def test_set_args_invalid_format(self):
        action = Action(app_name='HelloWorld', action_name='Add Three',
                        arguments=[Argument('num1', value='-5.6'),
                                   Argument('num2', value='4.3'),
                                   Argument('num3', value='10.2')])
        with self.assertRaises(InvalidArgument):
            action.set_arguments(
                [Argument('num1', value='-5.62'), Argument('num2', value='5'), Argument('num3', value='invalid')])

    def test_execute_with_triggers(self):
        triggers = [Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])]
        action = Action(app_name='HelloWorld', action_name='helloWorld', triggers=triggers)
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        action.send_data_to_trigger({"data_in": {"data": 'aaa'}})

        result = {'triggered': False}

        def callback_is_sent(sender, **kwargs):
            if kwargs['event'] == WalkoffEvent.TriggerActionTaken:
                result['triggered'] = True

        WalkoffEvent.CommonWorkflowSignal.connect(callback_is_sent)
        action.execute(instance.instance, {})
        self.assertTrue(result['triggered'])

    def test_execute_multiple_triggers(self):
        triggers = [Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])]
        action = Action(app_name='HelloWorld', action_name='helloWorld', triggers=triggers)
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        action.send_data_to_trigger({"data_in": {"data": 'a'}})

        trigger_taken = {'triggered': 0}
        trigger_not_taken = {'triggered': 0}

        def callback_is_sent(sender, **kwargs):
            if kwargs['event'] == WalkoffEvent.TriggerActionTaken:
                trigger_taken['triggered'] += 1
            elif kwargs['event'] == WalkoffEvent.TriggerActionNotTaken:
                action.send_data_to_trigger({"data_in": {"data": 'aaa'}})
                trigger_not_taken['triggered'] += 1

        WalkoffEvent.CommonWorkflowSignal.connect(callback_is_sent)

        action.execute(instance.instance, {})
        self.assertEqual(trigger_taken['triggered'], 1)
        self.assertEqual(trigger_not_taken['triggered'], 1)
