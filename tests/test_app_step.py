import unittest
import json

from core.appinstance import AppInstance
from core.case.callbacks import data_sent
import core.config.config
import core.config.paths
from core.decorators import ActionResult
from core.executionelements.appstep import AppStep
from core.executionelements.step_2 import Step
from core.helpers import (import_all_apps, UnknownApp, UnknownAppAction, InvalidInput, import_all_flags,
                          import_all_filters, get_app_action_api)
from tests.config import test_apps_path, function_api_path


class TestAppStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_apps(path=test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def __compare_init(self, elem, app, action, device='', inputs=None, widgets=None):
        self.assertEqual(elem.action, action)
        self.assertEqual(elem.app, app)
        action, api = get_app_action_api(app, action)
        self.assertEqual(elem._run, action)
        self.assertListEqual(elem._input_api, api)
        self.assertEqual(elem.device, device)
        inputs = inputs if inputs is not None else {}
        self.assertDictEqual({key: input_element for key, input_element in elem.inputs.items()}, inputs)
        widgets = widgets if widgets is not None else []
        self.assertEqual(len(elem.widgets), len(widgets))
        for widget in elem.widgets:
            self.assertIn((widget.app, widget.name), widgets)

    def test_init_super_class_is_constructed(self):
        step = AppStep('HelloWorld', 'helloWorld')
        self.assertIsInstance(step, Step)
        self.assertIsNotNone(step.uid)

    def test_init_app_action_only(self):
        step = AppStep('HelloWorld', 'helloWorld')
        self.__compare_init(step, 'HelloWorld', 'helloWorld')

    def test_init_app_and_action_name_different_than_method_name(self):
        step = AppStep(app='HelloWorld', action='Hello World')
        self.__compare_init(step, 'HelloWorld', 'Hello World')

    def test_init_invalid_app(self):
        with self.assertRaises(UnknownApp):
            AppStep('InvalidApp', 'helloWorld')

    def test_init_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            AppStep(app='HelloWorld', action='invalid')

    def test_init_app_action_only_with_device(self):
        step = AppStep('HelloWorld', 'helloWorld', device='test')
        self.__compare_init(step, 'HelloWorld', 'helloWorld', device='test')

    def test_init_with_inputs_no_conversion(self):
        step = AppStep('HelloWorld', 'returnPlusOne', inputs={'number': -5.6})
        self.__compare_init(step, 'HelloWorld', 'returnPlusOne', inputs={'number': -5.6})

    def test_init_with_inputs_with_conversion(self):
        step = AppStep('HelloWorld', 'returnPlusOne', inputs={'number': '-5.6'})
        self.__compare_init(step, 'HelloWorld', 'returnPlusOne', inputs={'number': -5.6})

    def test_init_with_invalid_input_name(self):
        with self.assertRaises(InvalidInput):
            AppStep('HelloWorld', 'returnPlusOne', inputs={'invalid': '-5.6'})

    def test_init_with_invalid_input_type(self):
        with self.assertRaises(InvalidInput):
            AppStep('HelloWorld', 'returnPlusOne', inputs={'number': 'invalid'})

    def test_init_with_widgets(self):
        widget_tuples = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        widgets = [{'app': widget[0], 'name': widget[1]} for widget in widget_tuples]
        step = AppStep('HelloWorld', 'helloWorld', widgets=widgets)
        self.__compare_init(step, 'HelloWorld', 'helloWorld', widgets=widget_tuples)

    def test_execute_no_args(self):
        step = AppStep(app='HelloWorld', action='helloWorld')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        self.assertEqual(step.execute(instance.instance, {}), ActionResult({'message': 'HELLO WORLD'}, 'Success'))
        self.assertEqual(step._output, ActionResult({'message': 'HELLO WORLD'}, 'Success'))

    def test_execute_generates_uid(self):
        step = AppStep(app='HelloWorld', action='helloWorld')
        original_execution_uid = step.get_execution_uid()
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        step.execute(instance.instance, {})
        self.assertNotEqual(step.get_execution_uid(), original_execution_uid)

    def test_execute_with_args(self):
        step = AppStep(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_sends_callbacks(self):
        step = AppStep(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        result = {'started_triggered': False, 'result_triggered': False}

        @data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, AppStep):
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
        step = AppStep(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_with_accumulator_with_extra_steps(self):
        step = AppStep(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_with_accumulator_missing_step(self):
        step = AppStep(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(InvalidInput):
            step.execute(instance.instance, accumulator)

    def test_execute_with_accumulator_missing_step_callbacks(self):
        step = AppStep(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        result = {'started_triggered': False, 'result_triggered': False}

        @data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, AppStep):
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
        step = AppStep(app='HelloWorld', action='Json Sample',
                       inputs={'json_in': {'a': '-5.6', 'b': {'a': '4.3', 'b': 5.3}, 'c': ['1', '2', '3'],
                                        'd': [{'a': '', 'b': 3}, {'a': '', 'b': -1.5}, {'a': '', 'b': -0.5}]}})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 11.0)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step._output, result)

    def test_execute_action_which_raises_exception(self):
        from tests.apps.HelloWorld.exceptions import CustomException
        step = AppStep(app='HelloWorld', action='Buggy')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(CustomException):
            step.execute(instance.instance, {})

    def test_execute_action_which_raises_exception_sends_callbacks(self):
        from tests.apps.HelloWorld.exceptions import CustomException
        step = AppStep(app='HelloWorld', action='Buggy')
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        result = {'started_triggered': False}

        @data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, AppStep):
                self.assertIs(sender, step)
                self.assertIn('callback_name', kwargs)
                self.assertEqual(kwargs['callback_name'], 'Step Started')
                self.assertIn('object_type', kwargs)
                self.assertEqual(kwargs['object_type'], 'Step')
                result['started_triggered'] = True

        with self.assertRaises(CustomException):
            step.execute(instance.instance, {})

        self.assertTrue(result['started_triggered'])

    def test_execute_event(self):
        step = AppStep(app='HelloWorld', action='Sample Event', inputs={'arg1': 1})
        instance = AppInstance.create(app_name='HelloWorld', device_name='device1')

        import time
        from tests.apps.HelloWorld.events import event1
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
        step = AppStep(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        step.set_input({'num1': '-5.62', 'num2': '5', 'num3': '42.42'})
        self.assertDictEqual(step.inputs, {'num1': -5.62, 'num2': 5., 'num3': 42.42})

    def test_set_input_invalid_name(self):
        step = AppStep(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'invalid': '5', 'num3': '42.42'})

    def test_set_input_invalid_format(self):
        step = AppStep(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'num2': '5', 'num3': 'invalid'})
