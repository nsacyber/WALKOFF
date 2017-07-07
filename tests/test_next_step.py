import unittest
from core.nextstep import NextStep
from core.flag import Flag
from core.helpers import import_all_filters, import_all_flags, import_all_apps
from tests.config import test_apps_path, function_api_path
import core.config.config
from tests.apps import App
from core.decorators import ActionResult

class TestNextStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        App.registry = {}
        import_all_apps(path=test_apps_path, reload=True)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def __compare_init(self, elem, name, parent_name, flags, ancestry, status='Success'):
        self.assertEqual(elem.status, status)
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.parent_name, parent_name)
        self.assertListEqual([flag.action for flag in elem.flags], [flag['action'] for flag in flags])
        for flag, expected in zip(elem.flags, flags):
            self.assertDictEqual(flag.as_json(), expected)
        self.assertListEqual(elem.ancestry, ancestry)

    def test_init(self):
        next_step = NextStep()
        self.__compare_init(next_step, '', '', [], ['', ''])

    def test_init_with_name(self):
        next_step = NextStep(name='name')
        self.__compare_init(next_step, 'name', '', [], ['', 'name'])

    def test_init_with_status(self):
        next_step = NextStep(name='name', status='test_status')
        self.__compare_init(next_step, 'name', '', [], ['', 'name'], status='test_status')

    def test_init_with_name_and_parent(self):
        next_step = NextStep(name='name', parent_name='parent')
        self.__compare_init(next_step, 'name', 'parent', [], ['parent', 'name'])

    def test_init_with_name_and_parent_and_ancestry(self):
        next_step = NextStep(name='name', parent_name='parent', ancestry=['a', 'b'])
        self.__compare_init(next_step, 'name', 'parent', [], ['a', 'b', 'name'])

    def test_init_with_empty_flags(self):
        next_step = NextStep(name='name', parent_name='parent', flags=[], ancestry=['a', 'b'])
        self.__compare_init(next_step, 'name', 'parent', [], ['a', 'b', 'name'])

    def test_init_with_flags(self):
        flags = [Flag(action='Top Flag'), Flag(action='mod1_flag1')]
        expected_flag_json = [{'action': 'Top Flag', 'args': {}, 'filters': []},
                              {'action': 'mod1_flag1', 'args': {}, 'filters': []}]
        next_step = NextStep(name='name', parent_name='parent', flags=flags, ancestry=['a', 'b'])
        self.__compare_init(next_step, 'name', 'parent', expected_flag_json, ['a', 'b', 'name'])

    def test_as_json_with_children(self):
        self.assertDictEqual(NextStep().as_json(), {'name': '', 'status': 'Success', 'flags': []})

    def test_as_json_without_children(self):
        self.assertDictEqual(NextStep().as_json(with_children=False), {'name': '', 'status': 'Success', 'flags': []})

    def test_as_json_with_children_with_name(self):
        self.assertDictEqual(NextStep(name='name1').as_json(), {'name': 'name1', 'status': 'Success', 'flags': []})

    def test_as_json_without_children_with_name(self):
        self.assertDictEqual(NextStep(name='name1').as_json(with_children=False),
                             {'name': 'name1', 'status': 'Success', 'flags': []})

    def test_as_json_with_children_with_status(self):
        self.assertDictEqual(NextStep(status='test_status').as_json(),
                             {'name': '', 'status': 'test_status', 'flags': []})

    def test_as_json_without_children_with_status(self):
        self.assertDictEqual(NextStep(status='test_status').as_json(with_children=False),
                             {'name': '', 'status': 'test_status', 'flags': []})

    def test_as_json_with_children_full(self):
        flags = [Flag(action='Top Flag'), Flag(action='mod1_flag1')]
        expected_flag_json = [{'action': 'Top Flag', 'args': {}, 'filters': []},
                              {'action': 'mod1_flag1', 'args': {}, 'filters': []}]
        self.assertDictEqual(NextStep(name='name1', flags=flags).as_json(),
                             {'name': 'name1', 'status': 'Success', 'flags': expected_flag_json})

    def test_as_json_without_children_full(self):
        flags = [Flag(action='Top Flag'), Flag(action='mod1_flag1')]
        expected_flag_json = ['Top Flag', 'mod1_flag1']
        self.assertDictEqual(NextStep(name='name1', flags=flags).as_json(with_children=False),
                             {'name': 'name1', 'status': 'Success', 'flags': expected_flag_json})

    def test_from_json_name_only(self):
        json_in = {'name': 'name1', 'flags': []}
        next_step = NextStep.from_json(json_in)
        self.__compare_init(next_step, 'name1', '', [], ['', 'name1'])

    def test_from_json_with_status(self):
        json_in = {'name': 'name1', 'status': 'test_status', 'flags': []}
        next_step = NextStep.from_json(json_in)
        self.__compare_init(next_step, 'name1', '', [], ['', 'name1'], status='test_status')

    def test_from_json_with_parent(self):
        json_in = {'name': 'name1', 'flags': []}
        next_step = NextStep.from_json(json_in, parent_name='parent')
        self.__compare_init(next_step, 'name1', 'parent', [], ['parent', 'name1'])

    def test_from_json_with_ancestry(self):
        json_in = {'name': 'name1', 'flags': []}
        next_step = NextStep.from_json(json_in, ancestry=['a', 'b'])
        self.__compare_init(next_step, 'name1', '', [], ['a', 'b', 'name1'])

    def test_from_json_with_parent_and_ancestry(self):
        json_in = {'name': 'name1', 'flags': []}
        next_step = NextStep.from_json(json_in, parent_name='parent', ancestry=['a', 'b'])
        self.__compare_init(next_step, 'name1', 'parent', [], ['a', 'b', 'name1'])

    def test_from_json_with_flags(self):
        flag_json = [{'action': 'Top Flag', 'args': {}, 'filters': []},
                     {'action': 'mod1_flag1', 'args': {}, 'filters': []}]
        next_step = NextStep.from_json({'name': 'name1', 'flags': flag_json})
        self.__compare_init(next_step, 'name1', '', flag_json, ['', 'name1'])

    def test_to_xml_no_flags(self):
        next_step = NextStep(name='name')
        xml = next_step.to_xml()
        self.assertEqual(xml.tag, 'next')
        self.assertEqual(xml.get('step'), 'name')
        self.assertEqual(len(xml.findall('flag')), 0)

    def test_to_xml_error_no_flags(self):
        next_step = NextStep(name='name')
        xml = next_step.to_xml(tag='error')
        self.assertEqual(xml.tag, 'error')
        self.assertEqual(xml.get('step'), 'name')
        self.assertEqual(len(xml.findall('flag')), 0)

    def test_to_xml_with_status(self):
        next_step = NextStep(name='name', status='test_status')
        xml = next_step.to_xml()
        self.assertEqual(xml.tag, 'next')
        self.assertEqual(xml.get('step'), 'name')
        status_xml = xml.findall('status')
        self.assertEqual(len(status_xml), 1)
        self.assertEqual(status_xml[0].text, 'test_status')
        self.assertEqual(len(xml.findall('flag')), 0)

    def test_to_xml(self):
        flags = [Flag(action='Top Flag'), Flag(action='mod1_flag1')]
        next_step = NextStep(name='name', flags=flags)
        xml = next_step.to_xml()
        self.assertEqual(xml.tag, 'next')
        self.assertEqual(xml.get('step'), 'name')
        self.assertEqual(len(xml.findall('flag')), 2)

    def test_to_xml_error(self):
        flags = [Flag(action='Top Flag'), Flag(action='mod1_flag1')]
        next_step = NextStep(name='name', flags=flags)
        xml = next_step.to_xml(tag='error')
        self.assertEqual(xml.tag, 'error')
        self.assertEqual(xml.get('step'), 'name')
        self.assertEqual(len(xml.findall('flag')), 2)

    def test_to_from_xml_is_convertible(self):
        flags = [Flag(action='mod1_flag1'), Flag(action='Top Flag')]
        inputs = [NextStep(),
                  NextStep(name='name'),
                  NextStep(status='TestStatus'),
                  NextStep(name='name', parent_name='parent'),
                  NextStep(name='name', parent_name='parent', ancestry=['a', 'b']),
                  NextStep(name='name', parent_name='parent', flags=[], ancestry=['a', 'b']),
                  NextStep(name='name', parent_name='parent', flags=flags, ancestry=['a', 'b'])]
        for next_step in inputs:
            original_json = next_step.as_json()
            new_step = NextStep(xml=next_step.to_xml())
            new_json = new_step.as_json()
            self.assertDictEqual(new_json, original_json)

    def test_to_xml_none(self):
        next_step = NextStep()
        next_step.name = None
        self.assertIsNone(next_step.to_xml())

    def test_eq(self):
        flags = [Flag(action='mod1_flag1'), Flag(action='Top Flag')]
        next_steps = [NextStep(),
                      NextStep(name='name'),
                      NextStep(status='TestStatus'),
                      NextStep(name='name', parent_name='parent', flags=flags, ancestry=['a', 'b'])]
        for i in range(len(next_steps)):
            for j in range(len(next_steps)):
                if i == j:
                    self.assertEqual(next_steps[i], next_steps[j])
                else:
                    self.assertNotEqual(next_steps[i], next_steps[j])

    def test_call(self):
        flags1 = [Flag(action='regMatch', args={'regex': '(.*)'})]
        flags2 = [Flag(action='regMatch', args={'regex': '(.*)'}),
                  Flag(action='regMatch', args={'regex': 'a'})]

        inputs = [('name1', [], ActionResult('aaaa', 'Success'), True),
                  ('name2', flags1, ActionResult('anyString', 'Success'), True),
                  ('name3', flags2, ActionResult('anyString', 'Success'), True),
                  ('name4', flags2, ActionResult('bbbb', 'Success'), False),
                  ('name4', flags2, ActionResult('aaaa', 'Custom'), False)]

        for name, flags, input_str, expect_name in inputs:
            next_step = NextStep(name=name, flags=flags)
            if expect_name:
                expected_name = next_step.name
                self.assertEqual(next_step(input_str, {}), expected_name)
            else:
                self.assertIsNone(next_step(input_str, {}))

    def test_get_children(self):
        next_step1 = NextStep()
        names = ['sub1_top_flag', 'mod1_flag1', 'Top Flag']
        for name in names:
            self.assertIsNone(next_step1.get_children([name]))
            self.assertDictEqual(next_step1.get_children([]), next_step1.as_json(with_children=False))

        flags = [Flag('sub1_top_flag'), Flag(action='mod1_flag1'), Flag(action='Top Flag')]
        next_step2 = NextStep(flags=flags)
        for i, name in enumerate(names):
            self.assertDictEqual(next_step2.get_children([name]), flags[i].as_json())
            self.assertDictEqual(next_step2.get_children([]), next_step2.as_json(with_children=False))

    def test_name_parent_rename(self):
        next_step = NextStep(ancestry=['nextstep_parent'], name='nextstep')
        new_ancestry = ['nextstep_parent_update']
        next_step.reconstruct_ancestry(new_ancestry)
        new_ancestry.append('nextstep')
        self.assertListEqual(new_ancestry, next_step.ancestry)

    def test_name_parent_flag_rename(self):
        next_step = NextStep(ancestry=['nextstep_parent'], name='nextstep')
        flag = Flag(action="Top Flag", ancestry=next_step.ancestry)
        next_step.flags = [flag]

        new_ancestry = ["nextstep_parent_update"]
        next_step.reconstruct_ancestry(new_ancestry)
        new_ancestry.append("nextstep")
        new_ancestry.append("Top Flag")
        self.assertListEqual(new_ancestry, next_step.flags[0].ancestry)

    def test_name_parent_multiple_flag_rename(self):
        next_step = NextStep(ancestry=['nextstep_parent'], name='mod1_flag1')
        flag_one = Flag(action="Top Flag", ancestry=next_step.ancestry)
        flag_two = Flag(action="mod1_flag1", ancestry=next_step.ancestry)
        next_step.flags = [flag_one, flag_two]

        new_ancestry = ["nextstep_parent_update"]
        next_step.reconstruct_ancestry(new_ancestry)
        new_ancestry.append("mod1_flag1")
        new_ancestry.append("Top Flag")
        self.assertListEqual(new_ancestry, next_step.flags[0].ancestry)

        new_ancestry.remove("Top Flag")
        new_ancestry.append("mod1_flag1")
        self.assertListEqual(new_ancestry, next_step.flags[1].ancestry)
