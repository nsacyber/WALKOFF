import unittest
from core.helpers import (import_all_filters, import_all_flags, InvalidInput,
                          InvalidElementConstructed, UnknownFlag, UnknownFilter)
import core.config.config
from core.flag import Flag
from core.filter import Filter
from tests.config import function_api_path


class TestFlag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def __compare_init(self, flag, action, parent_name, ancestry, filters, args):
        self.assertEqual(flag.action, action)
        self.assertEqual(flag.parent_name, parent_name)
        self.assertListEqual(flag.ancestry, ancestry)
        self.assertEqual(len(flag.filters), len(filters))
        for actual_filter, expected_filter in zip(flag.filters, filters):
            self.assertDictEqual(actual_filter.as_json(), expected_filter.as_json())
        self.assertDictEqual(flag.args, args)

    def test_init_no_args_action_only(self):
        flag = Flag(action='Top Flag')
        self.__compare_init(flag, 'Top Flag', '', ['', 'Top Flag'], [], {})

    def test_init_no_args_with_parent(self):
        flag = Flag(action='Top Flag', parent_name='test_parent')
        self.__compare_init(flag, 'Top Flag', 'test_parent', ['test_parent', 'Top Flag'], [], {})

    def test_init_no_args_with_ancestry(self):
        flag = Flag(action='Top Flag', ancestry=['a', 'b'])
        self.__compare_init(flag, 'Top Flag', '', ['a', 'b', 'Top Flag'], [], {})

    def test_init_no_args_with_parent_and_ancestry(self):
        flag = Flag(parent_name='test_parent', action='Top Flag', ancestry=['a', 'b'])
        self.__compare_init(flag, 'Top Flag', 'test_parent', ['a', 'b', 'Top Flag'], [], {})

    def test_init_with_args_with_conversion(self):
        flag = Flag(action='mod1_flag2', args={'arg1': '3'})
        self.__compare_init(flag, 'mod1_flag2', '', ['', 'mod1_flag2'], [], {'arg1': 3})

    def test_init_with_args_no_conversion(self):
        flag = Flag(action='mod1_flag2', args={'arg1': 3})
        self.__compare_init(flag, 'mod1_flag2', '', ['', 'mod1_flag2'], [], {'arg1': 3})

    def test_init_with_args_invalid_arg_name(self):
        with self.assertRaises(InvalidInput):
            Flag(action='mod1_flag2', args={'invalid': '3'})

    def test_init_with_args_invalid_arg_type(self):
        with self.assertRaises(InvalidInput):
            Flag(action='mod1_flag2', args={'arg1': 'aaa'})

    def test_init_with_filters(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='Top Flag', filters=filters)
        self.__compare_init(flag, 'Top Flag', '', ['', 'Top Flag'], filters, {})

    def test_init_with_no_action_no_xml(self):
        with self.assertRaises(InvalidElementConstructed):
            Flag()

    def test_as_json_action_only_with_children(self):
        flag = Flag(action='Top Flag')
        expected = {'action': 'Top Flag', 'args': {}, 'filters': []}
        self.assertDictEqual(flag.as_json(), expected)

    def test_as_json_action_only_without_children(self):
        flag = Flag(action='Top Flag')
        expected = {'action': 'Top Flag', 'args': {}, 'filters': []}
        self.assertDictEqual(flag.as_json(with_children=False), expected)

    def test_as_json_with_args_with_children(self):
        flag = Flag(action='mod1_flag2', args={'arg1': '11113'})
        expected = {'action': 'mod1_flag2', 'args': {'arg1': 11113}, 'filters': []}
        self.assertDictEqual(flag.as_json(), expected)

    def test_as_json_with_args_without_children(self):
        flag = Flag(action='mod1_flag2', args={'arg1': '11113'})
        expected = {'action': 'mod1_flag2', 'args': {'arg1': 11113}, 'filters': []}
        self.assertDictEqual(flag.as_json(with_children=False), expected)

    def test_as_json_with_args_and_filters_with_children(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='mod1_flag2', args={'arg1': '11113'}, filters=filters)
        filters_json = [filter_element.as_json() for filter_element in flag.filters]
        expected = {'action': 'mod1_flag2', 'args': {'arg1': 11113}, 'filters': filters_json}
        self.assertDictEqual(flag.as_json(), expected)

    def test_as_json_with_args_and_filters_without_children(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='mod1_flag2', args={'arg1': '11113'}, filters=filters)
        filters_json = [filter_element.name for filter_element in flag.filters]
        expected = {'action': 'mod1_flag2', 'args': {'arg1': 11113}, 'filters': filters_json}
        self.assertDictEqual(flag.as_json(with_children=False), expected)

    def test_to_xml_action_only(self):
        xml = Flag(action='Top Flag').to_xml()
        self.assertEqual(xml.tag, 'flag')
        self.assertEqual(xml.get('action'), 'Top Flag')
        self.assertListEqual(xml.findall('args/*'), [])
        self.assertListEqual(xml.findall('filters/*'), [])

    def test_to_xml_with_args_no_filters(self):
        xml = Flag(action='mod1_flag2', args={'arg1': '5'}).to_xml()
        self.assertEqual(xml.tag, 'flag')
        self.assertEqual(xml.get('action'), 'mod1_flag2')
        arg_xml = xml.findall('args/*')
        self.assertEqual(len(arg_xml), 1)
        self.assertEqual(arg_xml[0].tag, 'arg1')
        self.assertEqual(arg_xml[0].text, 5)
        self.assertListEqual(xml.findall('filters/*'), [])

    def test_to_xml_with_args_and_filters(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='mod1_flag2', args={'arg1': '5'}, filters=filters)
        xml = flag.to_xml()
        self.assertEqual(xml.tag, 'flag')
        self.assertEqual(xml.get('action'), 'mod1_flag2')
        arg_xml = xml.findall('args/*')
        self.assertEqual(len(arg_xml), 1)
        self.assertEqual(arg_xml[0].tag, 'arg1')
        self.assertEqual(arg_xml[0].text, 5)
        filter_xml = xml.findall('filters/*')
        self.assertEqual(len(filter_xml), 2)
        self.assertTrue(all(filter_elem_xml.tag == 'filter' for filter_elem_xml in filter_xml))
        self.assertListEqual([filter_elem_xml.get('action') for filter_elem_xml in filter_xml],
                             ['mod1_filter2', 'Top Filter'])
        filter1_args = filter_xml[0].findall('args/*')
        self.assertEqual(len(filter1_args), 1)
        self.assertEqual(filter1_args[0].tag, 'arg1')
        self.assertEqual(filter1_args[0].text, 5.4)
        filter2_args = filter_xml[1].findall('args/*')
        self.assertEqual(len(filter2_args), 0)

    def __assert_xml_is_convertible(self, flag):
        original_json = flag.as_json()
        original_xml = flag.to_xml()
        new_flag = Flag(xml=original_xml)
        self.assertDictEqual(new_flag.as_json(), original_json)

    def test_to_from_xml_is_same_action_only(self):
        self.__assert_xml_is_convertible(Flag(action='Top Flag'))

    def test_to_from_xml_is_same_with_args(self):
        self.__assert_xml_is_convertible(Flag(action='mod1_flag2', args={'arg1': '5'}))

    def test_to_from_xml_is_same_with_args_and_filters(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        self.__assert_xml_is_convertible(Flag(action='mod1_flag2', args={'arg1': '5'}, filters=filters))

    def test_call_action_only_no_args_valid_data_no_conversion(self):
        self.assertTrue(Flag(action='Top Flag')(3.4))

    def test_call_action_only_no_args_valid_data_with_conversion(self):
        self.assertTrue(Flag(action='Top Flag')('3.4'))

    def test_call_action_only_no_args_invalid_data(self):
        self.assertFalse(Flag(action='Top Flag')('invalid'))

    def test_call_action_with_valid_args_valid_data(self):
        self.assertTrue(Flag(action='mod1_flag2', args={'arg1': 3})('5'))

    def test_call_action_with_valid_args_invalid_data(self):
        self.assertFalse(Flag(action='mod1_flag2', args={'arg1': 3})('invalid'))

    def test_call_action_with_valid_args_and_filters_valid_data(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5'}), Filter(action='Top Filter')]
        # should go <input = 1> -> <mod1_filter2 = 5+1 = 6> -> <Top Filter 6=6> -> <mod1_flag2 4+6%2==0> -> True
        self.assertTrue(Flag(action='mod1_flag2', args={'arg1': 4}, filters=filters)('1'))

    def test_call_action_with_valid_args_and_filters_invalid_data(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5'}), Filter(action='Top Filter')]
        # should go <input = invalid> -> <mod1_filter2 with error = invalid> -> <Top Filter with error = invalid>
        # -> <mod1_flag2 4+invalid throws error> -> False
        self.assertFalse(Flag(action='mod1_flag2', args={'arg1': 4}, filters=filters)('invalid'))

    def test_from_json_action_only(self):
        json_in = {'action': 'Top Flag', 'args': {}, 'filters': []}
        flag = Flag.from_json(json_in)
        self.__compare_init(flag, 'Top Flag', '', ['', 'Top Flag'], [], {})

    def test_from_json_invalid_action(self):
        json_in = {'action': 'invalid', 'args': {}, 'filters': []}
        with self.assertRaises(UnknownFlag):
            Flag.from_json(json_in)

    def test_from_json_action_only_with_parent(self):
        json_in = {'action': 'Top Flag', 'args': {}, 'filters': []}
        flag = Flag.from_json(json_in, parent_name='parent')
        self.__compare_init(flag, 'Top Flag', 'parent', ['parent', 'Top Flag'], [], {})

    def test_from_json_action_only_with_parent_and_ancestry(self):
        json_in = {'action': 'Top Flag', 'args': {}, 'filters': []}
        flag = Flag.from_json(json_in, parent_name='parent', ancestry=['a', 'b'])
        self.__compare_init(flag, 'Top Flag', 'parent', ['a', 'b', 'Top Flag'], [], {})

    def test_from_json_with_args(self):
        json_in = {'action': 'mod1_flag2', 'args': {'arg1': 3}, 'filters': []}
        flag = Flag.from_json(json_in, parent_name='parent', ancestry=['a', 'b'])
        self.__compare_init(flag, 'mod1_flag2', 'parent', ['a', 'b', 'mod1_flag2'], [], {'arg1': 3})

    def test_from_json_with_invalid_args(self):
        json_in = {'action': 'mod1_flag2', 'args': {'invalid': 3}, 'filters': []}
        with self.assertRaises(InvalidInput):
            Flag.from_json(json_in, parent_name='parent', ancestry=['a', 'b'])

    def test_from_json_with_filters(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        filters_json = [filter_elem.as_json() for filter_elem in filters]
        json_in = {'action': 'mod1_flag2', 'args': {'arg1': 3}, 'filters': filters_json}
        flag = Flag.from_json(json_in, parent_name='parent', ancestry=['a', 'b'])
        self.__compare_init(flag, 'mod1_flag2', 'parent', ['a', 'b', 'mod1_flag2'], filters, {'arg1': 3})
        for filter_element in flag.filters:
            self.assertEqual(filter_element.parent_name, 'mod1_flag2')
            self.assertListEqual(filter_element.ancestry, ['a', 'b', 'mod1_flag2', filter_element.action])

    def test_from_json_with_filters_with_invalid_action(self):
        filters_json = [{'action': 'Top Filter', 'args': {}}, {'action': 'invalid', 'args': {'arg1': '5.4'}}]
        json_in = {'action': 'mod1_flag2', 'args': {'arg1': 3}, 'filters': filters_json}
        with self.assertRaises(UnknownFilter):
            Flag.from_json(json_in, parent_name='parent', ancestry=['a', 'b'])

    def test_from_json_with_filters_with_invalid_args(self):
        filters_json = [{'action': 'Top Filter', 'args': {}}, {'action': 'mod1_filter2', 'args': {'arg1': 'invalid'}}]
        json_in = {'action': 'mod1_flag2', 'args': {'arg1': 3}, 'filters': filters_json}
        with self.assertRaises(InvalidInput):
            Flag.from_json(json_in, parent_name='parent', ancestry=['a', 'b'])

    def test_get_children_no_filters_no_ancestry(self):
        flag = Flag(action='Top Flag')
        self.assertDictEqual(flag.get_children([]), flag.as_json(with_children=False))

    def test_get_children_no_filters_with_ancestry(self):
        for ancestry in [['a'], ['a', 'b']]:
            self.assertIsNone(Flag(action='Top Flag').get_children(ancestry))

    def test_get_children_with_filters_no_ancestry(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='Top Flag', filters=filters)
        self.assertDictEqual(flag.get_children([]), flag.as_json(with_children=False))

    def test_get_children_with_filters_invalid_ancestry(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='Top Flag', filters=filters)
        for ancestry in [['a'], ['a', 'b']]:
            self.assertIsNone(flag.get_children(ancestry))

    def test_get_children_with_filters_valid_ancestry(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='Top Flag', filters=filters)
        self.assertDictEqual(flag.get_children(['mod1_filter2']), filters[0].as_json())
        self.assertDictEqual(flag.get_children(['Top Filter']), filters[1].as_json())

    def test_get_children_with_filters_ancestry_too_deep(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='Top Flag', filters=filters)
        for name in ['mod1_filter2', 'Top Filter']:
            self.assertIsNone(flag.get_children([name, 'too deep']))

    def test_reconstruct_ancestry_no_filters(self):
        flag = Flag(ancestry=['parent'], action='Top Flag')
        new_ancestry = ['parent_update']
        flag.reconstruct_ancestry(new_ancestry)
        new_ancestry.append('Top Flag')
        self.assertListEqual(flag.ancestry, new_ancestry)

    def test_reconstruct_ancestry_with_filters(self):
        filters = [Filter(action='mod1_filter2', args={'arg1': '5.4'}), Filter(action='Top Filter')]
        flag = Flag(action='Top Flag', filters=filters, ancestry=['flag_parent'])
        new_ancestry = ['new_parent']
        flag.reconstruct_ancestry(new_ancestry)
        new_ancestry.append('Top Flag')
        self.assertListEqual(flag.ancestry, new_ancestry)
        for filter_element in filters:
            ancestry = list(new_ancestry)
            ancestry.append(filter_element.action)
            self.assertEqual(filter_element.ancestry, ancestry)
