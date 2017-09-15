import unittest
from core.helpers import (import_all_filters, import_all_flags, InvalidInput,
                          InvalidElementConstructed, UnknownFlag, UnknownFilter)
import core.config.config
from core.flag import Flag
from core.filter import Filter
from tests.config import function_api_path
import uuid


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
            self.assertDictEqual(actual_filter.as_json(), expected_filter.as_json())
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

    def test_init_with_no_action_no_xml(self):
        with self.assertRaises(InvalidElementConstructed):
            Flag()

    def test_as_json_action_only(self):
        uid = uuid.uuid4().hex
        flag = Flag(action='Top Flag', uid=uid)
        expected = {'action': 'Top Flag', 'args': [], 'filters': [], 'uid': uid}
        self.assertDictEqual(flag.as_json(), expected)

    def test_as_json_with_args(self):
        uid = uuid.uuid4().hex
        flag = Flag(action='mod1_flag2', args={'arg1': '11113'}, uid=uid)
        expected = {'action': 'mod1_flag2', 'args': [{'name': 'arg1', 'value': 11113}],
                    'filters': [], 'uid': uid}
        self.assertDictEqual(flag.as_json(), expected)

    def test_as_json_with_args_and_filters(self):
        uid = uuid.uuid4().hex
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='mod1_flag2', args={'arg1': '11113'}, filters=filters, uid=uid)
        filters_json = [filter_element.as_json() for filter_element in flag.filters]
        expected = {'action': 'mod1_flag2', 'args': [{'name': 'arg1', 'value': 11113}],
                    'filters': filters_json, 'uid': uid}
        self.assertDictEqual(flag.as_json(), expected)

    def test_call_action_only_no_args_valid_data_no_conversion(self):
        self.assertTrue(Flag(action='Top Flag')(3.4, {}))

    def test_call_action_only_no_args_valid_data_with_conversion(self):
        self.assertTrue(Flag(action='Top Flag')('3.4', {}))

    def test_call_action_only_no_args_invalid_data(self):
        self.assertFalse(Flag(action='Top Flag')('invalid', {}))

    def test_call_action_with_valid_args_valid_data(self):
        self.assertTrue(Flag(action='mod1_flag2', args={'arg1': 3})('5', {}))

    def test_call_action_with_valid_complex_args_valid_data(self):
        self.assertTrue(Flag(action='mod2_flag2', args={'arg1': {'a': '1', 'b': '5'}})('some_long_string', {}))

    def test_call_action_with_valid_args_invalid_data(self):
        self.assertFalse(Flag(action='mod1_flag2', args={'arg1': 3})('invalid', {}))

    def test_call_action_with_valid_args_and_filters_valid_data(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5'}), Filter(action='Top Filter')]
        # should go <input = 1> -> <mod1_filter2 = 5+1 = 6> -> <Top Filter 6=6> -> <mod1_flag2 4+6%2==0> -> True
        self.assertTrue(Flag(action='mod1_flag2', args={'arg1': 4}, filters=filters)('1', {}))

    def test_call_action_with_valid_args_and_filters_invalid_data(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5'}), Filter(action='Top Filter')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Filter with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        self.assertFalse(Flag(action='mod1_flag2', args={'arg1': 4}, filters=filters)('invalid', {}))

    def test_call_action_with_valid_args_and_filters_invalid_data_and_routing(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '@step1'}), Filter(action='Top Filter')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Filter with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        accumulator = {'step1': '5', 'step2': 4}
        self.assertFalse(Flag(action='mod1_flag2', args={'arg1': 4}, filters=filters)('invalid', accumulator))

    def test_from_json_action_only(self):
        json_in = {'action': 'Top Flag', 'args': [], 'filters': []}
        flag = Flag.from_json(json_in)
        self.__compare_init(flag, 'Top Flag', [], {})

    def test_from_json_invalid_action(self):
        json_in = {'action': 'invalid', 'args': [], 'filters': []}
        with self.assertRaises(UnknownFlag):
            Flag.from_json(json_in)

    def test_from_json_with_uid(self):
        uid = uuid.uuid4().hex
        json_in = {'action': 'Top Flag', 'args': [], 'filters': [], 'uid': uid}
        flag = Flag.from_json(json_in)
        self.__compare_init(flag, 'Top Flag', [], {}, uid=uid)

    def test_from_json_with_args(self):
        args = [{'name': 'arg1', 'value': 3}]
        json_in = {'action': 'mod1_flag2', 'args': args, 'filters': []}
        flag = Flag.from_json(json_in)
        self.__compare_init(flag, 'mod1_flag2', [], {'arg1': 3})

    def test_from_json_with_args_and_routing(self):
        args = [{'name': 'arg1', 'value': '@step1'}]
        json_in = {'action': 'mod1_flag2', 'args': args, 'filters': []}
        flag = Flag.from_json(json_in)
        self.__compare_init(flag, 'mod1_flag2', [], {'arg1': '@step1'})

    def test_from_json_with_invalid_args(self):
        args = [{'name': 'invalid', 'value': 3}]
        json_in = {'action': 'mod1_flag2', 'args': args, 'filters': []}
        with self.assertRaises(InvalidInput):
            Flag.from_json(json_in)

    def test_from_json_with_filters(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        filters_json = [filter_elem.as_json() for filter_elem in filters]
        args = [{'name': 'arg1', 'value': 3}]
        json_in = {'action': 'mod1_flag2', 'args': args, 'filters': filters_json}
        flag = Flag.from_json(json_in)
        self.__compare_init(flag, 'mod1_flag2', filters, {'arg1': 3})

    def test_from_json_with_filters_with_invalid_action(self):
        args = [{'name': 'arg1', 'value': 3}]
        filters_json = [{'action': 'Top Filter', 'args': []},
                        {'action': 'invalid', 'args': [{'name': 'arg1', 'value': 5.4}]}]
        json_in = {'action': 'mod1_flag2', 'args': args, 'filters': filters_json}
        with self.assertRaises(UnknownFilter):
            Flag.from_json(json_in)

    def test_from_json_with_filters_with_invalid_args(self):
        args = [{'name': 'arg1', 'value': 3}]
        filter2_args = [{'name': 'arg1', 'value': 'invalid'}]
        filters_json = [{'action': 'Top Filter', 'args': []}, {'action': 'mod1_filter2', 'args': filter2_args}]
        json_in = {'action': 'mod1_flag2', 'args': args, 'filters': filters_json}
        with self.assertRaises(InvalidInput):
            Flag.from_json(json_in)
