import unittest
import uuid

from core.executionelements.transform import Transform
from core.executionelements.condition import Condition
from core.argument import Argument
from core.helpers import InvalidArgument
from tests.config import test_apps_path
import core.config.config
import apps


class TestCondition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.clear_cache()
        apps.cache_apps(path=test_apps_path)
        core.config.config.load_app_apis(test_apps_path)

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def __compare_init(self, condition, app_name, action_name, transforms, arguments=None, uid=None):
        self.assertEqual(condition.app_name, app_name)
        self.assertEqual(condition.action_name, action_name)
        self.assertEqual(len(condition.transforms), len(transforms))
        for actual_transform, expected_transform in zip(condition.transforms, transforms):
            self.assertDictEqual(actual_transform.read(), expected_transform.read())
        arguments = {arg.name: arg for arg in arguments}
        if arguments:
            self.assertDictEqual(condition.arguments, arguments)
        if uid is None:
            self.assertIsNotNone(condition.uid)
        else:
            self.assertEqual(condition.uid, uid)

    def test_init_no_arguments_action_only(self):
        condition = Condition('HelloWorld', 'Top Condition')
        self.__compare_init(condition, 'HelloWorld', 'Top Condition', [], {})

    def test_init_with_uid(self):
        uid = uuid.uuid4().hex
        condition = Condition('HelloWorld', 'Top Condition', uid=uid)
        self.__compare_init(condition, 'HelloWorld', 'Top Condition', [], {}, uid=uid)

    def test_init_with_arguments_with_conversion(self):
        condition = Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value='3')])
        self.__compare_init(condition, 'HelloWorld', 'mod1_flag2', [], [Argument('arg1', value='3')])

    def test_init_with_arguments_no_conversion(self):
        condition = Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value='3')])
        self.__compare_init(condition, 'HelloWorld', 'mod1_flag2', [], [Argument('arg1', value='3')])

    def test_init_with_arguments_with_routing(self):
        condition = Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', reference='action2')])
        self.__compare_init(condition, 'HelloWorld', 'mod1_flag2', [], [Argument('arg1', reference="action2")])

    def test_init_with_arguments_invalid_arg_name(self):
        with self.assertRaises(InvalidArgument):
            Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('invalid', value='3')])

    def test_init_with_arguments_invalid_arg_type(self):
        with self.assertRaises(InvalidArgument):
            Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value='aaa')])

    def test_init_with_transforms(self):
        transforms = [Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='5.4')]),
                      Transform(app_name='HelloWorld', action_name='Top Transform')]
        condition = Condition('HelloWorld', action_name='Top Condition', transforms=transforms)
        self.__compare_init(condition, 'HelloWorld', 'Top Condition', transforms, {})

    def test_execute_action_only_no_arguments_valid_data_no_conversion(self):
        self.assertTrue(Condition('HelloWorld', 'Top Condition').execute(3.4, {}))

    def test_execute_action_only_no_arguments_valid_data_with_conversion(self):
        self.assertTrue(Condition('HelloWorld', 'Top Condition').execute('3.4', {}))

    def test_execute_action_only_no_arguments_invalid_data(self):
        self.assertFalse(Condition('HelloWorld', 'Top Condition').execute('invalid', {}))

    def test_execute_action_with_valid_arguments_valid_data(self):
        self.assertTrue(
            Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value=3)]).execute('5', {}))

    def test_execute_action_with_valid_complex_arguments_valid_data(self):
        self.assertTrue(Condition('HelloWorld', action_name='mod1_flag3',
                                  arguments=[Argument('arg1', value={'a': '1', 'b': '5'})]).execute('some_long_string',
                                                                                                    {}))

    def test_execute_action_with_valid_arguments_invalid_data(self):
        self.assertFalse(
            Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value=3)]).execute('invalid', {}))

    def test_execute_action_with_valid_arguments_and_transforms_valid_data(self):
        transforms = [Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='5')]),
                      Transform('HelloWorld', action_name='Top Transform')]
        # should go <input = 1> -> <mod1_filter2 = 5+1 = 6> -> <Top Transform 6=6> -> <mod1_flag2 4+6%2==0> -> True
        self.assertTrue(Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value=4)],
                                  transforms=transforms).execute('1', {}))

    def test_execute_action_with_valid_arguments_and_transforms_invalid_data(self):
        transforms = [Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='5')]),
                      Transform('HelloWorld', action_name='Top Transform')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Transform with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        self.assertFalse(Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value=4)],
                                   transforms=transforms).execute('invalid', {}))

    def test_execute_action_with_valid_arguments_and_transforms_invalid_data_and_routing(self):
        transforms = [Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', reference='action1')]),
                      Transform('HelloWorld', action_name='Top Transform')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Transform with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        accumulator = {'action1': '5', 'action2': 4}
        self.assertFalse(Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value=4)],
                                   transforms=transforms).execute('invalid', accumulator))
