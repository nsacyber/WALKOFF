import unittest

from core.nextstep import Next
from core.flag import Flag
from core.filter import Filter

class TestNextStep(unittest.TestCase):

    def test_from_json(self):
        filter_params = ['test_filter_action', '']
        flags_params = [('', []), ('test_action', []), ('test_action', filter_params)]
        input_params = [('', '', None, []), ('test_name', '', None, []), ('test_name', 'test_parent', None, []),
                        ('test_name', 'test_parent', ['a', 'b'], []), ('test_name', 'test_parent', ['a', 'b'], flags_params)]

        for (name, parent_name, ancestry, flag_params) in input_params:
            next_step = Next(name=name, parent_name=parent_name, ancestry=ancestry)
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
            derived_next_step = Next.from_json(next_step_json, parent_name=parent_name, ancestry=ancestry)
            self.assertDictEqual(derived_next_step.as_json(), next_step_json)
            self.assertEqual(next_step.parent_name, derived_next_step.parent_name)
            self.assertListEqual(next_step.ancestry, derived_next_step.ancestry)

            # check the ancestry of the flags
            original_flag_ancestries = [list(flag.ancestry) for flag in next_step.flags]
            derived_flag_ancestries = [list(flag.ancestry) for flag in derived_next_step.flags]
            self.assertEqual(len(original_flag_ancestries), len(derived_flag_ancestries))
            for original_flag_ancestry, derived_flag_ancestry in zip(original_flag_ancestries, derived_flag_ancestries):
                self.assertListEqual(derived_flag_ancestry, original_flag_ancestry)