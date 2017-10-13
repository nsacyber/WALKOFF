import unittest
import core.config.config
import core.config.paths
from core.case.callbacks import data_sent
from core.decorators import ActionResult
from core.executionelements.flag import Flag
from core.executionelements.nextstep import NextStep
from core.executionelements.step import Step
from core.helpers import import_all_apps, import_all_flags, import_all_filters
from tests.config import test_apps_path, function_api_path


class TestStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_apps(path=test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def __compare_init(self, elem, name='', next_steps=None, risk=0., position=None, uid=None, templated=False, raw_representation=None):
        self.assertEqual(elem.name, name)
        next_steps = next_steps if next_steps is not None else []
        self.assertListEqual([next_step.name for next_step in elem.next_steps], next_steps)
        self.assertEqual(elem.risk, risk)
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
        step = Step()
        self.__compare_init(step)

    def test_init_with_name(self):
        step = Step(name='test')
        self.__compare_init(step, name='test')

    def test_init_with_uid(self):
        step = Step(uid='test')
        self.__compare_init(step, uid='test')

    def test_init_with_next_steps(self):
        next_steps = [NextStep(name=i) for i in range(3)]
        step = Step(next_steps=next_steps)
        self.__compare_init(step, next_steps=list(range(3)))

    def test_init_with_position(self):
        step = Step(position={'x': 13, 'y': 42})
        self.__compare_init(step, position={'x': 13, 'y': 42})

    def test_init_with_risk(self):
        step = Step(risk=42)
        self.__compare_init(step, risk=42)

    def test_init_templated(self):
        step = Step(templated=True, raw_representation={'a': 42})
        self.__compare_init(step, templated=True, raw_representation={'a': 42})

    def test_get_next_step_no_next_steps(self):
        step = Step()
        self.assertIsNone(step.get_next_step({}))

    def test_get_next_step_invalid_step(self):
        flag = Flag(action='regMatch', args={'regex': 'aaa'})
        next_step = NextStep(name='next', flags=[flag], status='Success')
        step = Step(next_steps=[next_step])
        step._output = ActionResult(result='bbb', status='Success')
        self.assertIsNone(step.get_next_step({}))

    def test_get_next_step(self):
        flag = Flag(action='regMatch', args={'regex': 'aaa'})
        next_step = NextStep(name='next', flags=[flag], status='Success')
        step = Step(next_steps=[next_step])
        step._output = ActionResult(result='aaa', status='Success')

        result = {'triggered': False}

        @data_sent.connect
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

    def test_generate_execution_uid_none_existing(self):
        step = Step()
        original_uid = step._execution_uid
        step.generate_execution_uid()
        self.assertNotEqual(original_uid, step._execution_uid)

    def test_get_execution_uid(self):
        step = Step()
        step.generate_execution_uid()
        self.assertEqual(step.get_execution_uid(), step._execution_uid)

    def test_update_json_from_template_raises(self):
        step = Step()
        with self.assertRaises(NotImplementedError):
            step._update_json_from_template({})

    def test_execute_raises(self):
        step = Step()
        with self.assertRaises(NotImplementedError):
            step.execute('a', 'something')

            # def test_init_app_and_action_only(self):
    #     step = Step(app='HelloWorld', action='helloWorld')
    #     self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [])
    #
    # def test_init_with_uid(self):
    #     uid = uuid.uuid4().hex
    #     step = Step(app='HelloWorld', action='helloWorld', uid=uid)
    #     self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], uid=uid)
    #
    # def test_init_app_and_action_name_different_than_method_name(self):
    #     step = Step(app='HelloWorld', action='Hello World')
    #     self.__compare_init(step, '', 'Hello World', 'HelloWorld', '', {}, [], [])
    #
    # def test_init_invalid_app(self):
    #     with self.assertRaises(UnknownApp):
    #         Step(app='InvalidApp', action='helloWorld')
    #
    # def test_init_invalid_action(self):
    #     with self.assertRaises(UnknownAppAction):
    #         Step(app='HelloWorld', action='invalid')
    #
    # def test_init_with_inputs_no_conversion(self):
    #     step = Step(app='HelloWorld', action='returnPlusOne', inputs={'number': -5.6})
    #     self.__compare_init(step, '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6}, [], [])
    #
    # def test_init_with_inputs_with_conversion(self):
    #     step = Step(app='HelloWorld', action='returnPlusOne', inputs={'number': '-5.6'})
    #     self.__compare_init(step, '', 'returnPlusOne', 'HelloWorld', '', {'number': -5.6}, [], [])
    #
    # def test_init_with_invalid_input_name(self):
    #     with self.assertRaises(InvalidInput):
    #         Step(app='HelloWorld', action='returnPlusOne', inputs={'invalid': '-5.6'})
    #
    # def test_init_with_invalid_input_type(self):
    #     with self.assertRaises(InvalidInput):
    #         Step(app='HelloWorld', action='returnPlusOne', inputs={'number': 'invalid'})
    #
    # def test_init_with_name(self):
    #     step = Step(app='HelloWorld', action='helloWorld', name='name')
    #     self.__compare_init(step, 'name', 'helloWorld', 'HelloWorld', '', {}, [], [])
    #
    # def test_init_with_device(self):
    #     step = Step(app='HelloWorld', action='helloWorld', device='dev')
    #     self.__compare_init(step, '', 'helloWorld', 'HelloWorld', 'dev', {}, [], [])
    #
    # def test_init_with_none_device(self):
    #     step = Step(app='HelloWorld', action='helloWorld', device='None')
    #     self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [])
    #
    # def test_init_with_risk(self):
    #     step = Step(app='HelloWorld', action='helloWorld', risk=42.3)
    #     self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], risk=42.3)
    #
    # def test_init_with_widgets(self):
    #     widget_tuples = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
    #     widgets = [{'app': widget[0], 'name': widget[1]} for widget in widget_tuples]
    #     step = Step(app='HelloWorld', action='helloWorld', widgets=widgets)
    #     self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], widget_tuples)
    #
    # def test_init_with_widget_objects(self):
    #     widget_tuples = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
    #     widgets = [Widget(*widget) for widget in widget_tuples]
    #     step = Step(app='HelloWorld', action='helloWorld', widgets=widgets)
    #     self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], widget_tuples)
    #
    # def test_init_with_position(self):
    #     step = Step(app='HelloWorld', action='helloWorld', position={'x': -12.3, 'y': 485})
    #     self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [], [], position={'x': -12.3, 'y': 485})
    #
    # def test_init_with_next_steps(self):
    #     next_steps = [NextStep(), NextStep(name='name'), NextStep(name='name2')]
    #     step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps)
    #     self.__compare_init(step, '', 'helloWorld', 'HelloWorld', '', {}, [step.read() for step in next_steps], [])
    #
    # def test_execute_no_args(self):
    #     step = Step(app='HelloWorld', action='helloWorld')
    #     instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
    #     self.assertEqual(step.execute(instance.instance, {}), ActionResult({'message': 'HELLO WORLD'}, 'Success'))
    #     self.assertEqual(step._output, ActionResult({'message': 'HELLO WORLD'}, 'Success'))
    #
    # def test_execute_with_args(self):
    #     step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
    #     instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
    #     result = step.execute(instance.instance, {})
    #     self.assertAlmostEqual(result.result, 8.9)
    #     self.assertEqual(result.status, 'Success')
    #     self.assertEqual(step._output, result)
    #
    # def test_execute_with_accumulator_with_conversion(self):
    #     step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
    #     accumulator = {'1': '-5.6', 'step2': '4.3'}
    #     instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
    #     result = step.execute(instance.instance, accumulator)
    #     self.assertAlmostEqual(result.result, 8.9)
    #     self.assertEqual(result.status, 'Success')
    #     self.assertEqual(step._output, result)
    #
    # def test_execute_with_accumulator_with_extra_steps(self):
    #     step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
    #     accumulator = {'1': '-5.6', 'step2': '4.3', '3': '45'}
    #     instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
    #     result = step.execute(instance.instance, accumulator)
    #     self.assertAlmostEqual(result.result, 8.9)
    #     self.assertEqual(result.status, 'Success')
    #     self.assertEqual(step._output, result)
    #
    # def test_execute_with_accumulator_missing_step(self):
    #     step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '@1', 'num2': '@step2', 'num3': '10.2'})
    #     accumulator = {'1': '-5.6', 'missing': '4.3', '3': '45'}
    #     instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
    #     with self.assertRaises(InvalidInput):
    #         step.execute(instance.instance, accumulator)
    #
    # def test_execute_with_complex_inputs(self):
    #     step = Step(app='HelloWorld', action='Json Sample',
    #                 inputs={'json_in': {'a': '-5.6', 'b': {'a': '4.3', 'b': 5.3}, 'c': ['1', '2', '3'],
    #                                     'd': [{'a': '', 'b': 3}, {'a': '', 'b': -1.5}, {'a': '', 'b': -0.5}]}})
    #     instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
    #     result = step.execute(instance.instance, {})
    #     self.assertAlmostEqual(result.result, 11.0)
    #     self.assertEqual(result.status, 'Success')
    #     self.assertEqual(step._output, result)
    #
    # def test_execute_action_which_raises_exception(self):
    #     from tests.apps.HelloWorld.exceptions import CustomException
    #     step = Step(app='HelloWorld', action='Buggy')
    #     instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
    #     with self.assertRaises(CustomException):
    #         step.execute(instance.instance, {})
    #
    # def test_execute_event(self):
    #     step = Step(app='HelloWorld', action='Sample Event', inputs={'arg1': 1})
    #     instance = AppInstance.create(app_name='HelloWorld', device_name='device1')
    #
    #     import time
    #     from tests.apps.HelloWorld.events import event1
    #     import threading
    #
    #     def sender():
    #         time.sleep(0.1)
    #         event1.trigger(3)
    #
    #     thread = threading.Thread(target=sender)
    #     start = time.time()
    #     thread.start()
    #     result = step.execute(instance.instance, {})
    #     end = time.time()
    #     thread.join()
    #     self.assertEqual(result, ActionResult(4, 'Success'))
    #     self.assertGreater((end-start), 0.1)
    #
    # def test_get_next_step_no_next_steps(self):
    #     step = Step(app='HelloWorld', action='helloWorld')
    #     step._output = 'something'
    #     self.assertIsNone(step.get_next_step({}))
    #
    # def test_get_next_step(self):
    #     flag1 = [Flag(action='mod1_flag2', args={'arg1': '3'}), Flag(action='mod1_flag2', args={'arg1': '-1'})]
    #     next_steps = [NextStep(flags=flag1, name='name1'), NextStep(name='name2')]
    #     step = Step(app='HelloWorld', action='helloWorld', next_steps=next_steps)
    #     step._output = ActionResult(2, 'Success')
    #     self.assertEqual(step.get_next_step({}), 'name2')
    #     step._output = ActionResult(1, 'Success')
    #     self.assertEqual(step.get_next_step({}), 'name1')
    #
    # def test_set_input_valid(self):
    #     step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
    #     step.set_input({'num1': '-5.62', 'num2': '5', 'num3': '42.42'})
    #     self.assertDictEqual(step.inputs, {'num1': -5.62, 'num2': 5., 'num3': 42.42})
    #
    # def test_set_input_invalid_name(self):
    #     step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
    #     with self.assertRaises(InvalidInput):
    #         step.set_input({'num1': '-5.62', 'invalid': '5', 'num3': '42.42'})
    #
    # def test_set_input_invalid_format(self):
    #     step = Step(app='HelloWorld', action='Add Three', inputs={'num1': '-5.6', 'num2': '4.3', 'num3': '10.2'})
    #     with self.assertRaises(InvalidInput):
    #         step.set_input({'num1': '-5.62', 'num2': '5', 'num3': 'invalid'})
