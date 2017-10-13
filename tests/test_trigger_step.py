import unittest
import uuid

from core.flag import Flag

import core.config.config
import core.config.paths
from core.decorators import ActionResult
from core.executionelements.triggerstep import TriggerStep
from core.executionelements.step_2 import Step
from core.helpers import (import_all_apps, import_all_flags,
                          import_all_filters)
from tests.config import test_apps_path, function_api_path


class TestTriggerStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_apps(path=test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def __compare_flags(self, elem, flags=None):
        flags = flags if flags is not None else []
        self.assertEqual(len(elem.flags), len(flags))
        self.assertSetEqual({flag.action for flag in elem.flags}, set(flags))

    def test_init_super_class_is_constructed(self):
        step = TriggerStep('HelloWorld', 'helloWorld')
        self.assertIsInstance(step, Step)
        self.assertIsNotNone(step.uid)

    def test_init_default(self):
        step = TriggerStep()
        self.__compare_flags(step)

    def test_init_with_flags(self):
        flags = [Flag(action='regMatch', args={'regex': '(.*)'}),
                 Flag(action='regMatch', args={'regex': 'a'})]
        step = TriggerStep(flags=flags)
        self.__compare_flags(step, ['regMatch', 'regMatch'])

    def test_execute_no_flags(self):
        step = TriggerStep()
        self.assertTrue(step.execute(None, {}))

    def test_execute_with_flags(self):
        flags = [Flag(action='regMatch', args={'regex': 'aaa'})]
        step = TriggerStep(flags=flags)
        print(dir(flags[0]))
        print(flags[0].execute('aaa', {}))
        self.assertTrue(step.execute('aaa', {}))


    # def test_call(self):
    #     flags1 = [Flag(action='regMatch', args={'regex': '(.*)'})]
    #     flags2 = [Flag(action='regMatch', args={'regex': '(.*)'}),
    #               Flag(action='regMatch', args={'regex': 'a'})]
    #
    #     inputs = [('name1', [], ActionResult('aaaa', 'Success'), True),
    #               ('name2', flags1, ActionResult('anyString', 'Success'), True),
    #               ('name3', flags2, ActionResult('anyString', 'Success'), True),
    #               ('name4', flags2, ActionResult('bbbb', 'Success'), False),
    #               ('name4', flags2, ActionResult('aaaa', 'Custom'), False)]
    #
    #     for name, flags, input_str, expect_name in inputs:
    #         step = TriggerStep(action='helloWorld', flags=flags)
    #         if expect_name:
    #             expected_name = step.name
    #             self.assertEqual(step(input_str, {}), expected_name)
    #         else:
    #             self.assertIsNone(step(input_str, {}))
