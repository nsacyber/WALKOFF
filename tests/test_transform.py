import unittest

import walkoff.appgateway
import walkoff.config
from tests.config import APPS_PATH
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.transform import Transform
from walkoff.helpers import InvalidExecutionElement


class TestTransform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.appgateway.clear_cache()
        walkoff.appgateway.cache_apps(path=APPS_PATH)
        walkoff.config.load_app_apis(APPS_PATH)

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()

    def __compare_init(self, elem, app_name, action_name, arguments=None):
        arguments = arguments if arguments is not None else {}
        self.assertEqual(elem.app_name, app_name)
        self.assertEqual(elem.action_name, action_name)
        if arguments:
            self.assertListEqual(elem.arguments, arguments)

    def test_init_action_only(self):
        filter_elem = Transform('HelloWorld', 'Top Transform')
        self.__compare_init(filter_elem, 'HelloWorld', 'Top Transform')

    def test_init_invalid_action(self):
        with self.assertRaises(InvalidExecutionElement):
            Transform('HelloWorld', 'Invalid')

    def test_init_with_args(self):
        filter_elem = Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='5.4')])
        self.__compare_init(filter_elem, 'HelloWorld', 'mod1_filter2', arguments=[Argument('arg1', value='5.4')])

    def test_init_with_args_with_routing(self):
        filter_elem = Transform('HelloWorld', action_name='mod1_filter2',
                                arguments=[Argument('arg1', reference="action1")])
        self.__compare_init(filter_elem, 'HelloWorld', 'mod1_filter2',
                            arguments=[Argument('arg1', reference="action1")])

    def test_init_with_invalid_arg_name(self):
        with self.assertRaises(InvalidExecutionElement):
            Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('invalid', value='5.4')])

    def test_init_with_invalid_arg_type(self):
        with self.assertRaises(InvalidExecutionElement):
            Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='invalid')])

    def test_execute_with_no_args_no_conversion(self):
        self.assertAlmostEqual(Transform('HelloWorld', 'Top Transform').execute(5.4, {}), 5.4)

    def test_execute_with_no_args_with_conversion(self):
        self.assertAlmostEqual(Transform('HelloWorld', 'Top Transform').execute('-10.437', {}), -10.437)

    def test_execute_with_invalid_input(self):
        self.assertEqual(Transform('HelloWorld', 'Top Transform').execute('invalid', {}), 'invalid')

    def test_execute_with_filter_which_raises_exception(self):
        self.assertEqual(Transform('HelloWorld', 'sub1_filter3').execute('anything', {}), 'anything')

    def test_execute_with_args_no_conversion(self):
        self.assertAlmostEqual(
            Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='10.3')]).execute(
                '5.4', {}), 15.7)

    def test_execute_with_args_with_conversion(self):
        self.assertAlmostEqual(
            Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='10.3')]).execute(5.4,
                                                                                                                    {}),
            15.7)

    def test_execute_with_args_with_routing(self):
        self.assertAlmostEqual(
            Transform('HelloWorld', action_name='mod1_filter2',
                      arguments=[Argument('arg1', reference="action1")]).execute(5.4, {'action1': 10.3}),
            15.7)

    def test_execute_with_complex_args(self):
        original_filter = Transform('HelloWorld', action_name='sub1_filter1',
                                    arguments=[Argument('arg1', value={'a': '5.4', 'b': 'string_in'})])
        self.assertEqual(original_filter.execute(3, {}), '3.0 5.4 string_in')

    def test_call_with_nested_complex_args(self):
        args = [Argument('arg', value={'a': '4', 'b': 6, 'c': [1, 2, 3]})]
        original_filter = Transform('HelloWorld', action_name='complex', arguments=args)
        self.assertAlmostEqual(original_filter.execute(3, {}), 19.0)

    def test_call_with_args_invalid_input(self):
        self.assertEqual(
            Transform('HelloWorld', action_name='mod1_filter2', arguments=[Argument('arg1', value='10.3')]).execute(
                'invalid', {}),
            'invalid')
