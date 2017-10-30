import unittest
import uuid

import core.config.config
from core.executionelements.filter import Filter
from core.executionelements.flag import Flag
from core.helpers import import_all_filters, import_all_flags, InvalidInput
from tests.config import function_api_path


class TestFlag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def __compare_init(self, flag, action, filters, args, uid=None):
        self.assertEqual(flag.action, action)
        self.assertEqual(len(flag.filters), len(filters))
        for actual_filter, expected_filter in zip(flag.filters, filters):
            self.assertDictEqual(actual_filter.read(), expected_filter.read())
        self.assertDictEqual(flag.args, args)
        if uid is None:
            self.assertIsNotNone(flag.uid)
        else:
            self.assertEqual(flag.uid, uid)

    def test_init_no_args_action_only(self):
        flag = Flag(action='Top Flag')
        self.__compare_init(flag, 'Top Flag', [], {})

    def test_init_with_uid(self):
        uid = uuid.uuid4().hex
        flag = Flag(action='Top Flag', uid=uid)
        self.__compare_init(flag, 'Top Flag', [], {}, uid=uid)

    def test_init_with_args_with_conversion(self):
        flag = Flag(action='mod1_flag2', args={'arg1': '3'})
        self.__compare_init(flag, 'mod1_flag2', [], {'arg1': 3})

    def test_init_with_args_no_conversion(self):
        flag = Flag(action='mod1_flag2', args={'arg1': 3})
        self.__compare_init(flag, 'mod1_flag2', [], {'arg1': 3})

    def test_init_with_args_with_routing(self):
        flag = Flag(action='mod1_flag2', args={'arg1': '@step2'})
        self.__compare_init(flag, 'mod1_flag2', [], {'arg1': '@step2'})

    def test_init_with_args_invalid_arg_name(self):
        with self.assertRaises(InvalidInput):
            Flag(action='mod1_flag2', args={'invalid': '3'})

    def test_init_with_args_invalid_arg_type(self):
        with self.assertRaises(InvalidInput):
            Flag(action='mod1_flag2', args={'arg1': 'aaa'})

    def test_init_with_filters(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='Top Flag', filters=filters)
        self.__compare_init(flag, 'Top Flag', filters, {})

    def test_execute_action_only_no_args_valid_data_no_conversion(self):
        self.assertTrue(Flag(action='Top Flag').execute(3.4, {}))

    def test_execute_action_only_no_args_valid_data_with_conversion(self):
        self.assertTrue(Flag(action='Top Flag').execute('3.4', {}))

    def test_execute_action_only_no_args_invalid_data(self):
        self.assertFalse(Flag(action='Top Flag').execute('invalid', {}))

    def test_execute_action_with_valid_args_valid_data(self):
        self.assertTrue(Flag(action='mod1_flag2', args={'arg1': 3}).execute('5', {}))

    def test_execute_action_with_valid_complex_args_valid_data(self):
        self.assertTrue(Flag(action='mod2_flag2', args={'arg1': {'a': '1', 'b': '5'}}).execute('some_long_string', {}))

    def test_execute_action_with_valid_args_invalid_data(self):
        self.assertFalse(Flag(action='mod1_flag2', args={'arg1': 3}).execute('invalid', {}))

    def test_execute_action_with_valid_args_and_filters_valid_data(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5'}), Filter(action='Top Filter')]
        # should go <input = 1> -> <mod1_filter2 = 5+1 = 6> -> <Top Filter 6=6> -> <mod1_flag2 4+6%2==0> -> True
        self.assertTrue(Flag(action='mod1_flag2', args={'arg1': 4}, filters=filters).execute('1', {}))

    def test_execute_action_with_valid_args_and_filters_invalid_data(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5'}), Filter(action='Top Filter')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Filter with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        self.assertFalse(Flag(action='mod1_flag2', args={'arg1': 4}, filters=filters).execute('invalid', {}))

    def test_execute_action_with_valid_args_and_filters_invalid_data_and_routing(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '@step1'}), Filter(action='Top Filter')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Filter with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        accumulator = {'step1': '5', 'step2': 4}
        self.assertFalse(Flag(action='mod1_flag2', args={'arg1': 4}, filters=filters).execute('invalid', accumulator))
