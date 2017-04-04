import unittest

from core.nextstep import NextStep
from core.flag import Flag
from core.filter import Filter
from core.arguments import Argument


class TestNextStep(unittest.TestCase):

    def __compare_init(self, elem, name, parent_name, flags, ancestry):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.parent_name, parent_name)
        self.assertListEqual([flag.action for flag in elem.flags], [flag['action'] for flag in flags])
        for flag, expected in zip(elem.flags, flags):
            self.assertDictEqual(flag.as_json(), expected)
        self.assertListEqual(elem.ancestry, ancestry)

    def test_init(self):
        next_step = NextStep()
        self.__compare_init(next_step, '', '', [], ['', ''])

        next_step = NextStep(name='name')
        self.__compare_init(next_step, 'name', '', [], ['', 'name'])

        next_step = NextStep(name='name', parent_name='parent')
        self.__compare_init(next_step, 'name', 'parent', [], ['parent', 'name'])

        next_step = NextStep(name='name', parent_name='parent', ancestry=['a', 'b'])
        self.__compare_init(next_step, 'name', 'parent', [], ['a', 'b', 'name'])

        next_step = NextStep(name='name', parent_name='parent', flags=[], ancestry=['a', 'b'])
        self.__compare_init(next_step, 'name', 'parent', [], ['a', 'b', 'name'])

        flags = [Flag(), Flag(action='action')]
        expected_flag_json = [{'action': '', 'args': {}, 'filters': []},
                              {'action': 'action', 'args': {}, 'filters': []}]
        next_step = NextStep(name='name', parent_name='parent', flags=flags, ancestry=['a', 'b'])
        self.__compare_init(next_step, 'name', 'parent', expected_flag_json, ['a', 'b', 'name'])

    def test_to_from_xml(self):
        flags = [Flag(), Flag(action='action')]
        inputs = [NextStep(),
                  NextStep(name='name'),
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

    def test_create_flag(self):
        def test_help(next_step, expected):
            self.assertEqual(len(next_step.flags), len(expected))
            self.assertListEqual([flag.action for flag in next_step.flags], [flag['action'] for flag in expected])
            for flag, expected_flag in zip(next_step.flags, expected):
                self.assertDictEqual(flag.as_json(), expected_flag)
                self.assertEqual(flag.parent_name, 'name')
                expected_ancestry = list(next_step.ancestry)
                expected_ancestry.append(flag.name)
                self.assertListEqual(flag.ancestry, expected_ancestry)

        next_step = NextStep(name='name')
        next_step.create_flag('1')
        expected = [Flag(action='1').as_json()]
        test_help(next_step, expected)

        filters = [Filter(action='test_filter_action'), Filter()]
        next_step.create_flag('2', filters=filters)
        expected.append(Flag(action='2', filters=filters).as_json())
        test_help(next_step, expected)
        args = {'arg1': 'a', 'arg2': 3, 'arg3': u'abc'}
        args = {arg_name: Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                for arg_name, arg_value in args.items()}
        next_step.create_flag('3', filters=filters, args=args)
        expected.append(Flag(action='3', filters=filters, args=args).as_json())
        test_help(next_step, expected)

    def test_remove_flag(self):
        flags = [Flag(action=str(name)) for name in range(5)]
        next_step = NextStep(name='name', flags=flags)
        expected_flags = [flag.name for flag in flags]

        self.assertTrue(next_step.remove_flag())
        expected_flags = expected_flags[:-1]
        self.assertListEqual([flag.name for flag in next_step.flags], expected_flags)

        self.assertTrue(next_step.remove_flag(index=0))
        expected_flags = expected_flags[1:]
        self.assertListEqual([flag.name for flag in next_step.flags], expected_flags)

        self.assertFalse(next_step.remove_flag(index=5))
        self.assertListEqual([flag.name for flag in next_step.flags], expected_flags)

        self.assertFalse(next_step.remove_flag(index=-5))
        self.assertListEqual([flag.name for flag in next_step.flags], expected_flags)

        self.assertTrue(next_step.remove_flag(index=1))
        expected_flags = [expected_flags[0]] + expected_flags[2:]
        self.assertListEqual([flag.name for flag in next_step.flags], expected_flags)

        self.assertTrue(next_step.remove_flag(-1))
        expected_flags = expected_flags[:-1]
        self.assertListEqual([flag.name for flag in next_step.flags], expected_flags)

        self.assertTrue(next_step.remove_flag(0))
        expected_flags = []
        self.assertListEqual([flag.name for flag in next_step.flags], expected_flags)

    def test_eq(self):
        flags = [Flag(), Flag(action='action')]
        next_steps = [NextStep(),
                      NextStep(name='name'),
                      NextStep(name='name', parent_name='parent', flags=flags, ancestry=['a', 'b'])]
        for i in range(len(next_steps)):
            for j in range(len(next_steps)):
                if i == j:
                    self.assertEqual(next_steps[i], next_steps[j])
                else:
                    self.assertNotEqual(next_steps[i], next_steps[j])

    def test_call(self):

        flags1 = [Flag(action='regMatch', args={'regex': Argument(key='regex', value='(.*)', format='str')})]
        flags2 = [Flag(action='regMatch', args={'regex': Argument(key='regex', value='(.*)', format='str')}),
                  Flag(action='regMatch', args={'regex': Argument(key='regex', value='a', format='str')})]
        flags3 = [Flag(action='invalidName', args={'regex': Argument(key='regex', value='(.*)', format='str')})]
        flags4 = [Flag(action='regMatch', args={'regex': Argument(key='regex', value='(.*)', format='str')}),
                  Flag(action='invalidName', args={'regex': Argument(key='regex', value='(.*)', format='str')})]
        inputs = [('name1', [], 'aaaa', True),
                  ('name2', flags1, 'anyString', True),
                  ('name3', flags2, 'anyString', True),
                  ('name4', flags2, 'bbbb', False),
                  ('name5', flags3, 'anyString', False),
                  ('name6', flags4, 'anyString', False)]

        for name, flags, input_str, expect_name in inputs:
            next_step = NextStep(name=name, flags=flags)
            if expect_name:
                expected_name = next_step.name
                self.assertEqual(next_step(input_str), expected_name)
            else:
                self.assertIsNone(next_step(input_str))

    def test_to_from_json(self):
        filter_params = ['test_filter_action', '']
        flags_params = [('', []), ('test_action', []), ('test_action', filter_params)]
        input_params = [('', '', None, []), ('test_name', '', None, []), ('test_name', 'test_parent', None, []),
                        ('test_name', 'test_parent', ['a', 'b'], []),
                        ('test_name', 'test_parent', ['a', 'b'], flags_params)]

        for (name, parent_name, ancestry, flag_params) in input_params:
            next_step = NextStep(name=name, parent_name=parent_name, ancestry=ancestry)
            if flag_params:
                flags = []
                for flag_action, flag_filter_params in flag_params:
                    flag = Flag(action=flag_action, parent_name=next_step.name, ancestry=next_step.ancestry)
                    if filter_params:
                        flag.filters = [Filter(action=flag_action, parent_name=flag.name, ancestry=flag.ancestry)
                                        for flag_action in flag_filter_params]
                    flags.append(flag)
                next_step.flags = flags
            next_step_json = next_step.as_json()
            derived_next_step = NextStep.from_json(next_step_json, parent_name=parent_name, ancestry=ancestry)
            self.assertDictEqual(derived_next_step.as_json(), next_step_json)
            self.assertEqual(next_step.parent_name, derived_next_step.parent_name)
            self.assertListEqual(next_step.ancestry, derived_next_step.ancestry)

            derived_json_without_children = next_step_json
            derived_json_without_children['flags'] = [flag['action'] for flag in derived_json_without_children['flags']]
            self.assertDictEqual(derived_next_step.as_json(with_children=False), derived_json_without_children)

            # check the ancestry of the flags
            original_flag_ancestries = [list(flag.ancestry) for flag in next_step.flags]
            derived_flag_ancestries = [list(flag.ancestry) for flag in derived_next_step.flags]
            self.assertEqual(len(original_flag_ancestries), len(derived_flag_ancestries))
            for original_flag_ancestry, derived_flag_ancestry in zip(original_flag_ancestries, derived_flag_ancestries):
                self.assertListEqual(derived_flag_ancestry, original_flag_ancestry)
