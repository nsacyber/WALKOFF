import json
import unittest

import apps
import core.config.config
import core.config.paths
from core.case import callbacks
from core.decorators import ActionResult
from core.executionelements.condition import Condition
from core.executionelements.nextstep import NextStep
from core.helpers import UnknownApp, UnknownAppAction, InvalidInput
from core.appinstance import AppInstance
from core.executionelements.step import Step
from tests.config import test_apps_path


class TestStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def __compare_init(self, elem, name, action, app, device, inputs, triggers=None, next_steps=None,
                       widgets=None, risk=0., position=None, uid=None, templated=False, raw_representation=None):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.action, action)
        self.assertEqual(elem.app, app)
        self.assertEqual(elem.device, device)
        self.assertDictEqual({key: input_element for key, input_element in elem.inputs.items()}, inputs)
        next_steps = next_steps if next_steps is not None else []
        self.assertListEqual([next_step.name for next_step in elem.next_steps], next_steps)
        self.assertEqual(elem.risk, risk)
        widgets = widgets if widgets is not None else []
        self.assertEqual(len(elem.widgets), len(widgets))
        for widget in elem.widgets:
            self.assertIn((widget.app, widget.name), widgets)
        if triggers:
            self.assertEqual(len(elem.triggers), len(triggers))
            self.assertSetEqual({trigger.action for trigger in elem.triggers}, set(triggers))
        position = position if position is not None else {}
        self.assertDictEqual(elem.position, position)
        if templated:
            self.assertTrue(elem.templated)
            self.assertDictEqual(elem._raw_representation, raw_representation)
        else:
            self.assertFalse(elem.templated)
            self.assertDictEqual(elem._raw_representation, {})
        if uid is None:
            self.assertIsNotNone(elem.uid)
        else:
            self.assertEqual(elem.uid, uid)
        self.assertIsNone(elem._output)
        self.assertIsNone(elem._next_up)
        self.assertEqual(elem._execution_uid, 'default')

    def test_init_default(self):
        step = Step('HelloWorld', 'helloWorld')
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {})

    def test_init_with_name(self):
        step = Step('HelloWorld', 'helloWorld', name='test')
        self.__compare_init(step, 'test', 'helloWorld', 'HelloWorld', '', {})

    def test_init_with_uid(self):
        step = Step('HelloWorld', 'helloWorld', uid='test')
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, uid='test')

    def test_init_with_next_steps(self):
        next_steps = [NextStep(name=i) for i in range(3)]
        step = Step('HelloWorld', 'helloWorld', next_steps=next_steps)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, next_steps=list(range(3)))

    def test_init_with_position(self):
        step = Step('HelloWorld', 'helloWorld', position={'x': 13, 'y': 42})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, position={'x': 13, 'y': 42})

    def test_init_with_risk(self):
        step = Step('HelloWorld', 'helloWorld', risk=42)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, risk=42)

    def test_init_templated(self):
        step = Step('HelloWorld', 'helloWorld', templated=True, raw_representation={'a': 42})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, templated=True, raw_representation={'a': 42})

    def test_get_next_step_no_next_steps(self):
        step = Step('HelloWorld', 'helloWorld')
        self.assertIsNone(step.get_next_step({}))

    def test_get_next_step_invalid_step(self):
        flag = Condition('HelloWorld', 'regMatch', args={'regex': 'aaa'})
        next_step = NextStep(name='next', conditions=[flag], status='Success')
        step = Step('HelloWorld', 'helloWorld', next_steps=[next_step])
        step._output = ActionResult(result='bbb', status='Success')
        self.assertIsNone(step.get_next_step({}))

    def test_get_next_step(self):
        flag = Condition('HelloWorld', 'regMatch', args={'regex': 'aaa'})
        next_step = NextStep(name='next', conditions=[flag], status='Success')
        step = Step('HelloWorld', 'helloWorld', next_steps=[next_step])
        step._output = ActionResult(result='aaa', status='Success')

        result = {'triggered': False}

        @callbacks.data_sent.connect
        def validate_sent_data(sender, **kwargs):
            if isinstance(sender, Step):
                self.assertIs(sender, step)
                self.assertIn('callback_name', kwargs)
                self.assertEqual(kwargs['callback_name'], 'Conditionals Executed')
                self.assertIn('object_type', kwargs)
                self.assertEqual(kwargs['object_type'], 'Step')
                result['triggered'] = True

        self.assertEqual(step.get_next_step({}), 'next')
        self.assertEqual(step._next_up, 'next')
        self.assertTrue(result['triggered'])

    def test_get_execution_uid(self):
        step = Step('HelloWorld', 'helloWorld')
        self.assertEqual(step.get_execution_uid(), step._execution_uid)

    def test_init_super_class_is_constructed(self):
        step = Step('HelloWorld', 'helloWorld')
        self.assertIsInstance(step, Step)
        self.assertIsNotNone(step.uid)

    def test_init_app_action_only(self):
        step = Step('HelloWorld', 'helloWorld')
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {})

    def test_init_app_and_action_name_different_than_method_name(self):
        step = Step(app='HelloWorld', action='Hello World')
        self.__compare_init(step, '', 'Hello World', 'HelloWorld', '', {})

    def test_init_invalid_app(self):
        with self.assertRaises(UnknownApp):
            Step('InvalidApp', 'helloWorld')

    def test_init_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            Step(app='HelloWorld', action='invalid')

    def test_init_app_action_only_with_device(self):
        step = Step('HelloWorld', 'helloWorld', device='test')
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', 'test', {})

    def test_init_with_inputs_no_conversion(self):
        step = Step('HelloWorld', 'returnPlusOne', inputs={'number': -5.6})
        self.__compare_init(step, '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6})

    def test_init_with_inputs_with_conversion(self):
        step = Step('HelloWorld', 'returnPlusOne', inputs={'number': '-5.6'})
        self.__compare_init(step, '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6})

    def test_init_with_invalid_input_name(self):
        with self.assertRaises(InvalidInput):
            Step('HelloWorld', 'returnPlusOne', inputs={'invalid': '-5.6'})

    def test_init_with_invalid_input_type(self):
        with self.assertRaises(InvalidInput):
            Step('HelloWorld', 'returnPlusOne', inputs={'number': 'invalid'})

    def test_init_with_flags(self):
        triggers = [Condition('HelloWorld', 'regMatch', args={'regex': '(.*)'}),
                    Condition('HelloWorld', 'regMatch', args={'regex': 'a'})]
        step = Step('HelloWorld', 'helloWorld', triggers=triggers)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, triggers=['regMatch', 'regMatch'])

    def test_init_with_widgets(self):
        widget_tuples = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        widgets = [{'app': widget[0], 'name': widget[1]} for widget in widget_tuples]
        step = Step('HelloWorld', 'helloWorld', widgets=widgets)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, widgets=widget_tuples)

    def test_execute_no_args(self):
        step = Step(app='HelloWorld', action='helloWorld')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        self.assertEqual(step.execute(instance.instance, {}), ActionResult({'message': 'HELLO WORLD'}, 'Success'))
        self.assertEqual(step._output, ActionResult({'message': 'HELLO WORLD'}, 'Success'))

    def test_execute_generates_uid(self):
        step = Step(app='HelloWorld', action='helloWorld')
        original_execution_uid = step.get_execution_uid()
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        step.execute(instance.instance, {})
        self.assertNotEqual(step.get_execution_uid(), original_execution_uid)

    def test_execute_with_args(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_sends_callbacks(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        result = {'started_triggered': False, 'result_triggered': False}

        @callbacks.data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, Step):
                self.assertIs(sender, step)
                self.assertIn('callback_name', kwargs)
                self.assertIn(kwargs['callback_name'], ('Step Started', 'Function Execution Success'))
                self.assertIn('object_type', kwargs)
                self.assertEqual(kwargs['object_type'], 'Step')
                if kwargs['callback_name'] == 'Step Started':
                    result['started_triggered'] = True
                else:
                    self.assertIn('data', kwargs)
                    data = json.loads(kwargs['data'])
                    self.assertIn('result', data)
                    data = data['result']
                    self.assertEqual(data['status'], 'Success')
                    self.assertAlmostEqual(data['result'], 8.9)
                    result['result_triggered'] = True

        step.execute(instance.instance, {})
        self.assertTrue(result['started_triggered'])
        self.assertTrue(result['result_triggered'])

    def test_execute_with_accumulator_with_conversion(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_with_accumulator_with_extra_steps(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_with_accumulator_missing_step(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(InvalidInput):
            step.execute(instance.instance, accumulator)

    def test_execute_with_accumulator_missing_step_callbacks(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        result = {'started_triggered': False, 'result_triggered': False}

        @callbacks.data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, Step):
                self.assertIs(sender, step)
                self.assertIn('callback_name', kwargs)
                self.assertIn(kwargs['callback_name'], ('Step Started', 'Step Input Invalid'))
                self.assertIn('object_type', kwargs)
                self.assertEqual(kwargs['object_type'], 'Step')
                if kwargs['callback_name'] == 'Step Started':
                    result['started_triggered'] = True
                else:
                    result['result_triggered'] = True

        with self.assertRaises(InvalidInput):
            step.execute(instance.instance, accumulator)

        self.assertTrue(result['started_triggered'])
        self.assertTrue(result['result_triggered'])

    def test_execute_with_complex_inputs(self):
        step = Step(app='HelloWorld', action='Json Sample',
                    inputs={'json_in': {'a': '-5.6', 'b': {'a': '4.3', 'b': 5.3}, 'c': ['1', '2', '3'],
                                        'd': [{'a': '', 'b': 3}, {'a': '', 'b': -1.5}, {'a': '', 'b': -0.5}]}})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 11.0)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_action_which_raises_exception(self):
        from tests.testapps.HelloWorld.exceptions import CustomException
        step = Step(app='HelloWorld', action='Buggy')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(CustomException):
            step.execute(instance.instance, {})

    def test_execute_action_which_raises_exception_sends_callbacks(self):
        from tests.testapps.HelloWorld.exceptions import CustomException
        step = Step(app='HelloWorld', action='Buggy')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        result = {'started_triggered': False}

        @callbacks.data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, Step):
                self.assertIs(sender, step)
                self.assertIn('callback_name', kwargs)
                self.assertEqual(kwargs['callback_name'], 'Step Started')
                self.assertIn('object_type', kwargs)
                self.assertEqual(kwargs['object_type'], 'Step')
                result['started_triggered'] = True

        with self.assertRaises(CustomException):
            step.execute(instance.instance, {})

        self.assertTrue(result['started_triggered'])

    def test_execute_global_action(self):
        step = Step(app='HelloWorld', action='global2', inputs={'arg1': 'something'})
        instance = AppInstance.create(app_name='HelloWorld', device_name='')
        result = step.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 'something')
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_event(self):
        step = Step(app='HelloWorld', action='Sample Event', inputs={'arg1': 1})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        import time
        from tests.testapps.HelloWorld.events import event1
        import threading

        def sender():
            time.sleep(0.1)
            event1.trigger(3)

        thread = threading.Thread(target=sender)
        start = time.time()
        thread.start()
        result = step.execute(instance.instance, {})
        end = time.time()
        thread.join()
        self.assertEqual(result, ActionResult(4, 'Success'))
        self.assertGreater((end-start), 0.1)

    def test_set_input_valid(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        step.set_input({'num1': '-5.62', 'num2': '5', 'num3': '42.42'})
        self.assertDictEqual(step.inputs, {'num1': -5.62, 'num2': 5., 'num3': 42.42})

    def test_set_input_invalid_name(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'invalid': '5', 'num3': '42.42'})

    def test_set_input_invalid_format(self):
        step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'num2': '5', 'num3': 'invalid'})

    def test_execute_with_triggers(self):
        triggers = [Condition('HelloWorld', 'regMatch', args={'regex': 'aaa'})]
        step = Step(app='HelloWorld', action='helloWorld', triggers=triggers)
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        step.send_data_to_trigger({"data_in": {"data": 'aaa'}})

        result = {'triggered': False}

        @callbacks.data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if kwargs['callback_name'] == "Trigger Step Taken":
                result['triggered'] = True

        step.execute(instance.instance, {})
        self.assertTrue(result['triggered'])

    def test_execute_multiple_triggers(self):
        triggers = [Condition('HelloWorld', 'regMatch', args={'regex': 'aaa'})]
        step = Step(app='HelloWorld', action='helloWorld', triggers=triggers)
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        step.send_data_to_trigger({"data_in": {"data": 'a'}})

        trigger_taken = {'triggered': 0}
        trigger_not_taken = {'triggered': 0}

        @callbacks.data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if kwargs['callback_name'] == "Trigger Step Taken":
                trigger_taken['triggered'] += 1
            elif kwargs['callback_name'] == "Trigger Step Not Taken":
                step.send_data_to_trigger({"data_in": {"data": 'aaa'}})
                trigger_not_taken['triggered'] += 1

        step.execute(instance.instance, {})
        self.assertEqual(trigger_taken['triggered'], 1)
        self.assertEqual(trigger_not_taken['triggered'], 1)
