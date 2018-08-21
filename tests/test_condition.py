import unittest

import walkoff.appgateway
from tests.util import execution_db_help, initialize_test_config
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.condition import Condition
from walkoff.executiondb.transform import Transform
from walkoff.appgateway.apiutil import InvalidArgument
from walkoff.worker.action_exec_strategy import LocalActionExecutionStrategy


class TestCondition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        execution_db_help.setup_dbs()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()
        walkoff.appgateway.clear_cache()

    def __compare_init(self, condition, app_name, action_name, transforms, arguments=None, is_negated=False):
        self.assertEqual(condition.app_name, app_name)
        self.assertEqual(condition.action_name, action_name)
        self.assertEqual(len(condition.transforms), len(transforms))
        self.assertListEqual(condition.transforms, transforms)
        self.assertListEqual(condition.arguments, arguments)
        self.assertEqual(condition.is_negated, is_negated)

    def test_init_no_arguments_action_only(self):
        condition = Condition('HelloWorld', 'Top Condition')
        self.__compare_init(condition, 'HelloWorld', 'Top Condition', [], [])

    def test_init_no_arguments_inverted(self):
        condition = Condition('HelloWorld', 'Top Condition', is_negated=True)
        self.__compare_init(condition, 'HelloWorld', 'Top Condition', [], [], is_negated=True)

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
        condition = Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('invalid', value='3')])
        self.assertEqual(len(condition.errors), 2)

    def test_init_with_arguments_invalid_arg_type(self):
        condition = Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value='aaa')])
        self.assertEqual(len(condition.errors), 2)

    def test_init_with_transforms(self):
        transforms = [Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='5.4')]),
                      Transform(app_name='HelloWorld', action_name='Top Transform')]
        condition = Condition('HelloWorld', action_name='Top Condition', transforms=transforms)
        self.__compare_init(condition, 'HelloWorld', 'Top Condition', transforms, [])

    def test_execute_action_only_no_arguments_valid_data_no_conversion(self):
        self.assertTrue(Condition('HelloWorld', 'Top Condition').execute(LocalActionExecutionStrategy(), 3.4, {}))

    def test_execute_action_only_no_arguments_valid_data_with_conversion(self):
        self.assertTrue(Condition('HelloWorld', 'Top Condition').execute(LocalActionExecutionStrategy(), '3.4', {}))

    def test_execute_action_only_no_arguments_valid_data_with_conversion_inverted(self):
        self.assertFalse(Condition('HelloWorld', 'Top Condition', is_negated=True).execute(
            LocalActionExecutionStrategy(),
            '3.4',
            {})
        )

    def test_execute_action_only_no_arguments_invalid_data(self):
        self.assertFalse(
            Condition('HelloWorld', 'Top Condition').execute(LocalActionExecutionStrategy(), 'invalid', {}))

    def test_execute_action_with_valid_arguments_valid_data(self):
        self.assertTrue(
            Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value=3)]).execute(
                LocalActionExecutionStrategy(),
                '5',
                {})
        )

    def test_execute_action_with_valid_complex_arguments_valid_data(self):
        self.assertTrue(Condition('HelloWorld', action_name='mod1_flag3',
                                  arguments=[Argument('arg1', value={'a': '1', 'b': '5'})]).execute(
            LocalActionExecutionStrategy(),
            'some_long_string',
            {})
        )

    def test_execute_action_with_valid_arguments_invalid_data(self):
        self.assertFalse(
            Condition(
                'HelloWorld',
                action_name='mod1_flag2',
                arguments=[Argument('arg1', value=3)]).execute(LocalActionExecutionStrategy(), 'invalid', {}))

    def test_execute_action_with_valid_arguments_and_transforms_valid_data(self):
        transforms = [Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='5')]),
                      Transform('HelloWorld', action_name='Top Transform')]
        # should go <input = 1> -> <mod1_filter2 = 5+1 = 6> -> <Top Transform 6=6> -> <mod1_flag2 4+6%2==0> -> True
        self.assertTrue(Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value=4)],
                                  transforms=transforms).execute(LocalActionExecutionStrategy(), '1', {}))

    def test_execute_action_with_valid_arguments_and_transforms_invalid_data(self):
        transforms = [Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='5')]),
                      Transform('HelloWorld', action_name='Top Transform')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Transform with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        self.assertFalse(
            Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value=4)],
                      transforms=transforms).execute(LocalActionExecutionStrategy(), 'invalid', {}))

    def test_execute_action_with_valid_arguments_and_transforms_invalid_data_and_routing(self):
        transforms = [
            Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', reference='action1')]),
            Transform('HelloWorld', action_name='Top Transform')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Transform with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        accumulator = {'action1': '5', 'action2': 4}
        self.assertFalse(
            Condition('HelloWorld', action_name='mod1_flag2', arguments=[Argument('arg1', value=4)],
                      transforms=transforms).execute(LocalActionExecutionStrategy(), 'invalid', accumulator))
