import unittest
from core.filter import Filter
import core.config.config
from tests.config import function_api_path
from core.helpers import import_all_filters, import_all_flags, UnknownFilter, InvalidInput


class TestFilter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def compare_init(self, elem, action, parent_name, ancestry, args=None):
        args = args if args is not None else {}
        self.assertEqual(elem.action, action)
        self.assertDictEqual(elem.args, args)
        self.assertEqual(elem.name, elem.action)
        self.assertEqual(elem.parent_name, parent_name)
        self.assertListEqual(elem.ancestry, ancestry)

    def test_init_action_only(self):
        filter_elem = Filter(action='Top Filter')
        self.compare_init(filter_elem, 'Top Filter', '', ['', 'Top Filter'])

    def test_init_invalid_action(self):
        with self.assertRaises(UnknownFilter):
            Filter(action='Invalid')

    def test_init_action_with_parent(self):
        filter_elem = Filter(parent_name='test_parent', action='mod1_filter1')
        self.compare_init(filter_elem, 'mod1_filter1', 'test_parent', ['test_parent', 'mod1_filter1'])

    def test_init_with_ancestry(self):
        filter_elem = Filter(ancestry=['a', 'b'], action="mod1_filter1")
        self.compare_init(filter_elem, 'mod1_filter1', '', ['a', 'b', 'mod1_filter1'])

    def test_init_with_empty_ancestry(self):
        filter_elem = Filter(ancestry=[], action="mod1_filter1")
        self.compare_init(filter_elem, 'mod1_filter1', '', ['mod1_filter1'])

    def test_init_with_args(self):
        filter_elem = Filter(action='mod1_filter2', args={'arg1': '5.4'})
        self.compare_init(filter_elem, 'mod1_filter2', '', ['', 'mod1_filter2'], args={'arg1': 5.4})

    def test_init_with_invalid_arg_name(self):
        with self.assertRaises(InvalidInput):
            Filter(action='mod1_filter2', args={'invalid': '5.4'})

    def test_init_with_invalid_arg_type(self):
        with self.assertRaises(InvalidInput):
            Filter(action='mod1_filter2', args={'arg1': 'invalid'})

    def test_init_with_no_action_or_xml(self):
        with self.assertRaises(ValueError):
            Filter()

    def test_as_json_no_args(self):
        filter_elem = Filter(action='Top Filter')
        expected = {'action': 'Top Filter', 'args': {}}
        self.assertDictEqual(filter_elem.as_json(), expected)

    def test_as_json_with_args(self):
        filter_elem = Filter(action='mod1_filter2', args={'arg1': '-5.4'})
        expected = {'action': 'mod1_filter2', 'args': {'arg1': -5.4}}
        self.assertDictEqual(filter_elem.as_json(), expected)

    def test_to_xml_no_args(self):
        filter_elem = Filter(action='Top Filter')
        xml = filter_elem.to_xml()
        self.assertEqual(xml.tag, 'filter')
        self.assertEqual(xml.get('action'), 'Top Filter')
        self.assertListEqual(xml.findall('args/*'), [])

    def test_to_xml_with_args(self):
        filter_elem = Filter(action='mod1_filter2', args={'arg1': '5.4'})
        xml = filter_elem.to_xml()
        self.assertEqual(xml.tag, 'filter')
        self.assertEqual(xml.get('action'), 'mod1_filter2')
        arg_xml = xml.findall('args/*')
        self.assertEqual(len(arg_xml), 1)
        self.assertEqual(arg_xml[0].tag, 'arg1')
        self.assertEqual(arg_xml[0].text, 5.4)

    def __assert_xml_is_convertible(self, filter_elem):
        original_json = filter_elem.as_json()
        original_xml = filter_elem.to_xml()
        new_filter = Filter(xml=original_xml)
        self.assertDictEqual(new_filter.as_json(), original_json)

    def test_to_from_xml_are_same_no_args(self):
        original_filter = Filter(action='Top Filter')
        self.__assert_xml_is_convertible(original_filter)

    def test_to_from_xml_are_same_with_args(self):
        original_filter = Filter(action='mod1_filter2', args={'arg1': '5.4'})
        self.__assert_xml_is_convertible(original_filter)

    def test_from_json_no_args_default_parent_and_ancestry(self):
        json_in = {'action': 'Top Filter', 'args': {}}
        filter_elem = Filter.from_json(json_in)
        self.compare_init(filter_elem, 'Top Filter', '', ['', 'Top Filter'])

    def test_from_json_no_args_default_parent_with_ancestry(self):
        json_in = {'action': 'mod1_filter1', 'args': {}}
        filter_elem = Filter.from_json(json_in, ancestry=['a', 'b'])
        self.compare_init(filter_elem, 'mod1_filter1', '', ['a', 'b', 'mod1_filter1'])

    def test_from_json_no_args_with_parent_no_ancestry(self):
        json_in = {'action': 'mod1_filter1', 'args': {}}
        filter_elem = Filter.from_json(json_in, parent_name='test_parent')
        self.compare_init(filter_elem, 'mod1_filter1', 'test_parent', ['test_parent', 'mod1_filter1'])

    def test_from_json_no_args_with_parent_and_ancestry(self):
        json_in = {'action': 'mod1_filter1', 'args': {}}
        filter_elem = Filter.from_json(json_in, parent_name='test_parent', ancestry=['a', 'b'])
        self.compare_init(filter_elem, 'mod1_filter1', 'test_parent', ['a', 'b', 'mod1_filter1'])

    def test_from_json_with_args(self):
        json_in = {'action': 'mod1_filter2', 'args': {'arg1': '5.4'}}
        filter_elem = Filter.from_json(json_in, parent_name='test_parent', ancestry=['a', 'b'])
        self.compare_init(filter_elem, 'mod1_filter2', 'test_parent', ['a', 'b', 'mod1_filter2'], args={'arg1': 5.4})

    def test_call_with_no_args(self):
        self.assertIsNone(Filter(action='Top Filter')(5.4))

    def test_call_with_invalid_input(self):
        self.assertEqual(Filter(action='Top Filter')('invalid'), 'invalid')

    def test_call_with_filter_which_raises_exception(self):
        self.assertEqual(Filter(action='sub1_filter3')('anything'), 'anything')

    def test_name_parent_rename(self):
        filter = Filter(ancestry=['filter_parent'], action='Top Filter')
        new_ancestry = ['filter_parent_update']
        filter.reconstruct_ancestry(new_ancestry)
        new_ancestry.append('Top Filter')
        self.assertListEqual(filter.ancestry, new_ancestry)
