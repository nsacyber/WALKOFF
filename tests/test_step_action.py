import unittest
import socket
from core.flag import Flag
from core.stepaction import StepAction, _Widget
from core.nextstep import NextStep
from core.decorators import ActionResult
import core.config.config
import core.config.paths
from tests.config import test_apps_path, function_api_path
from core.instance import Instance
from core.helpers import (import_all_apps, UnknownApp, UnknownAppAction, InvalidInput, import_all_flags,
                          import_all_filters)
import uuid


class TestStepAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_apps(path=test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def setUp(self):
        self.uid = uuid.uuid4().hex
        self.basic_json = {'app': 'HelloWorld',
                           'action': 'helloWorld',
                           'device': '',
                           'name': '',
                           'next': [],
                           'position': {},
                           'inputs': [],
                           'widgets': [],
                           'risk': 0,
                           'uid': self.uid}
        self.basic_input_json = {'app': 'HelloWorld',
                                 'action': 'helloWorld',
                                 'name': '',
                                 'next': [],
                                 'position': {},
                                 'inputs': [],
                                 'uid': self.uid}

    def __compare_init(self, elem, name, action, app, device, inputs, next_steps,
                       widgets, risk=0., position=None, uid=None):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.action, action)
        self.assertEqual(elem.app, app)
        self.assertEqual(elem.device, device)
        self.assertDictEqual({key: input_element for key, input_element in elem.input.items()}, inputs)
        self.assertListEqual([conditional.as_json() for conditional in elem.conditionals], next_steps)
        self.assertEqual(elem.risk, risk)
        widgets = [_Widget(app, widget) for (app, widget) in widgets]
        self.assertEqual(len(elem.widgets), len(widgets))
        for widget in elem.widgets:
            self.assertIn(widget, widgets)
        position = position if position is not None else {}
        self.assertDictEqual(elem.position, position)
        self.assertIsNone(elem.output)
        self.assertFalse(elem.templated)
        if uid is None:
            self.assertIsNotNone(elem.uid)
        else:
            self.assertEqual(elem.uid, uid)

    def test_init_app_and_action_only(self):
        step = StepAction(app='HelloWorld', action='helloWorld')
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [])

    def test_init_with_uid(self):
        uid = uuid.uuid4().hex
        step = StepAction(app='HelloWorld', action='helloWorld', uid=uid)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], uid=uid)

    def test_init_app_and_action_name_different_than_method_name(self):
        step = StepAction(app='HelloWorld', action='Hello World')
        self.__compare_init(step, '', 'Hello World', 'HelloWorld', '', {}, [], [])

    def test_init_invalid_app(self):
        with self.assertRaises(UnknownApp):
            StepAction(app='InvalidApp', action='helloWorld')

    def test_init_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            StepAction(app='HelloWorld', action='invalid')

    def test_init_with_inputs_no_conversion(self):
        step = StepAction(app='HelloWorld', action='returnPlusOne', inputs={'number': -5.6})
        self.__compare_init(step, '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6}, [], [])

    def test_init_with_inputs_with_conversion(self):
        step = StepAction(app='HelloWorld', action='returnPlusOne', inputs={'number': '-5.6'})
        self.__compare_init(step, '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6}, [], [])

    def test_init_with_invalid_input_name(self):
        with self.assertRaises(InvalidInput):
            StepAction(app='HelloWorld', action='returnPlusOne', inputs={'invalid': '-5.6'})

    def test_init_with_invalid_input_type(self):
        with self.assertRaises(InvalidInput):
            StepAction(app='HelloWorld', action='returnPlusOne', inputs={'number': 'invalid'})

    def test_init_with_name(self):
        step = StepAction(app='HelloWorld', action='helloWorld', name='name')
        self.__compare_init(step, 'name', 'helloWorld', 'HelloWorld', '', {}, [], [])

    def test_init_with_device(self):
        step = StepAction(app='HelloWorld', action='helloWorld', device='dev')
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', 'dev', {}, [], [])

    def test_init_with_risk(self):
        step = StepAction(app='HelloWorld', action='helloWorld', risk=42.3)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], risk=42.3)

    def test_init_with_widgets(self):
        widgets = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        step = StepAction(app='HelloWorld', action='helloWorld', widgets=widgets)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], widgets)

    def test_init_with_position(self):
        step = StepAction(app='HelloWorld', action='helloWorld', position={'x': -12.3, 'y': 485})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], position={'x': -12.3, 'y': 485})

    def test_init_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = StepAction(app='HelloWorld', action='helloWorld', next_steps=next_steps)
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [step.as_json() for step in next_steps], [])

    def test_as_json(self):
        step = StepAction(app='HelloWorld', action='helloWorld', uid=self.uid)
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_name(self):
        step = StepAction(app='HelloWorld', action='helloWorld', name='name', uid=self.uid)
        self.basic_json['name'] = 'name'
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_device(self):
        step = StepAction(app='HelloWorld', action='helloWorld', device='device', uid=self.uid)
        self.basic_json['device'] = 'device'
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_risk(self):
        step = StepAction(app='HelloWorld', action='helloWorld', risk=120.6, uid=self.uid)
        self.basic_json['risk'] = 120.6
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_inputs(self):
        step = StepAction(app='HelloWorld', action='returnPlusOne', inputs={'number': '-5.6'}, uid=self.uid)
        self.basic_json['action'] = 'returnPlusOne'
        self.basic_json['inputs'] = [{'name': 'number', 'value': -5.6}]
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        step = StepAction(app='HelloWorld', action='helloWorld', next_steps=next_steps, uid=self.uid)
        self.basic_json['next'] = [next_step.as_json() for next_step in next_steps]
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_position(self):
        step = StepAction(app='HelloWorld', action='helloWorld', position={'x': -12.3, 'y': 485}, uid=self.uid)
        self.basic_json['position'] = {'x': -12.3, 'y': 485}
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_widgets(self):
        widgets = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        step = StepAction(app='HelloWorld', action='helloWorld', widgets=widgets, uid=self.uid)
        self.basic_json['widgets'] = [{'app': widget[0], 'name': widget[1]} for widget in widgets]
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_after_executed(self):
        step = StepAction(app='HelloWorld', action='helloWorld', uid=self.uid)
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        step.execute(instance.instance, {})
        step_json = step.as_json()
        self.assertDictEqual(step_json['output'], ActionResult({'message': 'HELLO WORLD'}, 'Success').as_json())

    def test_from_json_app_and_action_only(self):
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [])

    def test_from_json_with_uid(self):
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], uid=self.uid)

    def test_from_json_invalid_app(self):
        self.basic_input_json['app'] = 'Invalid'
        with self.assertRaises(UnknownApp):
            StepAction.from_json(self.basic_input_json, {})

    def test_from_json_invalid_action(self):
        self.basic_input_json['action'] = 'invalid'
        with self.assertRaises(UnknownAppAction):
            StepAction.from_json(self.basic_input_json, {})

    def test_from_json_with_name(self):
        self.basic_input_json['name'] = 'name1'
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, 'name1', 'helloWorld', 'HelloWorld', '', {}, [], [])

    def test_from_json_with_risk(self):
        self.basic_input_json['risk'] = 132.3
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], risk=132.3)

    def test_from_json_with_device(self):
        self.basic_input_json['device'] = 'device1'
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', 'device1', {}, [], [])

    def test_from_json_with_device_is_none(self):
        self.basic_input_json['device'] = None
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [])

    def test_from_json_with_device_is_none_string(self):
        self.basic_input_json['device'] = 'None'
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [])

    def test_from_json_with_widgets(self):
        widget_json = [{'name': 'widget_name', 'app': 'app1'}, {'name': 'w2', 'app': 'app2'}]
        widget_tuples = [('app1', 'widget_name'), ('app2', 'w2')]
        self.basic_input_json['widgets'] = widget_json
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], widget_tuples)

    def test_from_json_with_inputs(self):
        self.basic_input_json['action'] = 'Add Three'
        self.basic_input_json['inputs'] = [{'name': 'num1', 'value': '-5.6'}, {'name': 'num2', 'value': '4.3'},
                                           {'name': 'num3', 'value': '-10.265'}]
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'Add Three', 'HelloWorld', '',
                            {'num1': -5.6, 'num2': 4.3, 'num3': -10.265}, [], [])

    def test_from_json_with_inputs_invalid_name(self):
        self.basic_input_json['action'] = 'Add Three'
        self.basic_input_json['inputs'] = [{'name': 'num1', 'value': '-5.6'}, {'name': 'invalid', 'value': '4.3'},
                                           {'name': 'num3', 'value': '-10.265'}]
        with self.assertRaises(InvalidInput):
            StepAction.from_json(self.basic_input_json, {})

    def test_from_json_with_inputs_invalid_format(self):
        self.basic_input_json['action'] = 'Add Three'
        self.basic_input_json['inputs'] = [{'name': 'num1', 'value': '-5.6'}, {'name': 'num2', 'value': '4.3'},
                                           {'name': 'num3', 'value': 'invalid'}]
        with self.assertRaises(InvalidInput):
            StepAction.from_json(self.basic_input_json, {})

    def test_from_json_with_step_routing(self):
        self.basic_input_json['action'] = 'Add Three'
        self.basic_input_json['inputs'] = [{'name': 'num1', 'value': '-5.6'}, {'name': 'num2', 'value': '@step1'},
                                           {'name': 'num3', 'value': '@step2'}]
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'Add Three', 'HelloWorld', '',
                            {'num1': -5.6, 'num2': '@step1', 'num3': '@step2'}, [], [])

    def test_from_json_with_position(self):
        step = StepAction.from_json(self.basic_input_json, {'x': 125.3, 'y': 198.7})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], position={'x': 125.3, 'y': 198.7})

    def test_from_json_with_next_steps(self):
        next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
        next_steps_json = [next_step.as_json() for next_step in next_steps]
        self.basic_input_json['next'] = next_steps_json
        step = StepAction.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, next_steps_json, [])

    def test_execute_no_args(self):
        step = StepAction(app='HelloWorld', action='helloWorld')
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        self.assertEqual(step.execute(instance.instance, {}), ActionResult({'message': 'HELLO WORLD'}, 'Success'))
        self.assertEqual(step.output, ActionResult({'message': 'HELLO WORLD'}, 'Success'))

    def test_execute_with_args(self):
        step = StepAction(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step.output, result)

    def test_execute_with_accumulator_with_conversion(self):
        step = StepAction(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3'}
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step.output, result)

    def test_execute_with_accumulator_with_extra_steps(self):
        step = StepAction(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'step2': '4.3', '3': '45'}
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, accumulator)
        self.assertAlmostEqual(result.result, 8.9)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step.output, result)

    def test_execute_with_accumulator_missing_step(self):
        step = StepAction(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
        accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(InvalidInput):
            step.execute(instance.instance, accumulator)

    def test_execute_with_complex_inputs(self):
        step = StepAction(app='HelloWorld', action='Json Sample',
                    inputs={'json_in': {'a': '-5.6', 'b': {'a': '4.3', 'b': 5.3}, 'c': ['1', '2', '3'],
                                        'd': [{'a': '', 'b': 3}, {'a': '', 'b': -1.5}, {'a': '', 'b': -0.5}]}})
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        result = step.execute(instance.instance, {})
        self.assertAlmostEqual(result.result, 11.0)
        self.assertEqual(result.status, 'Success')
        self.assertEqual(step.output, result)

    def test_execute_action_which_raises_exception(self):
        from tests.apps.HelloWorld.exceptions import CustomException
        step = StepAction(app='HelloWorld', action='Buggy')
        instance = Instance.create(app_name='HelloWorld', device_name='device1')
        with self.assertRaises(CustomException):
            step.execute(instance.instance, {})

    def test_execute_event(self):
        step = StepAction(app='HelloWorld', action='Sample Event', inputs={'arg1': 1})
        instance = Instance.create(app_name='HelloWorld', device_name='device1')

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

    def test_get_next_step_no_next_steps(self):
        step = StepAction(app='HelloWorld', action='helloWorld')
        step.output = 'something'
        self.assertIsNone(step.get_next_step({}))

    def test_get_next_step(self):
        flag1 = [Flag(action='mod1_flag2', args={'arg1': '3'}), Flag(action='mod1_flag2', args={'arg1': '-1'})]
        next_steps = [NextStep(flags=flag1, name='name1'), NextStep(name='name2')]
        step = StepAction(app='HelloWorld', action='helloWorld', next_steps=next_steps)
        step.output = ActionResult(2, 'Success')
        self.assertEqual(step.get_next_step({}), 'name2')
        step.output = ActionResult(1, 'Success')
        self.assertEqual(step.get_next_step({}), 'name1')

    def test_set_input_valid(self):
        step = StepAction(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        step.set_input({'num1': '-5.62', 'num2': '5', 'num3': '42.42'})
        self.assertDictEqual(step.input, {'num1': -5.62, 'num2': 5., 'num3': 42.42})

    def test_set_input_invalid_name(self):
        step = StepAction(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'invalid': '5', 'num3': '42.42'})

    def test_set_input_invalid_format(self):
        step = StepAction(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
        with self.assertRaises(InvalidInput):
            step.set_input({'num1': '-5.62', 'num2': '5', 'num3': 'invalid'})
