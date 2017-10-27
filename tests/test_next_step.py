import unittest
import uuid

import apps
import core.config.config
from core.decorators import ActionResult
from core.executionelements.flag import Flag
from core.executionelements.nextstep import NextStep
from core.helpers import import_all_filters, import_all_flags
from tests.config import test_apps_path, function_api_path


class TestNextStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def __compare_init(self, elem, name, flags, status='Success', uid=None):
        self.assertEqual(elem.status, status)
        self.assertEqual(elem.name, name)
        self.assertListEqual([flag.action for flag in elem.flags], [flag['action'] for flag in flags])
        if uid is None:
            self.assertIsNotNone(elem.uid)
        else:
            self.assertEqual(elem.uid, uid)

    def test_init(self):
        next_step = NextStep()
        self.__compare_init(next_step, '', [])

    def test_init_wth_uid(self):
        uid = uuid.uuid4().hex
        next_step = NextStep(uid=uid)
        self.__compare_init(next_step, '', [], uid=uid)

    def test_init_with_name(self):
        next_step = NextStep(name='name')
        self.__compare_init(next_step, 'name', [])

    def test_init_with_status(self):
        next_step = NextStep(name='name', status='test_status')
        self.__compare_init(next_step, 'name', [], status='test_status')

    def test_init_with_empty_flags(self):
        next_step = NextStep(name='name', flags=[])
        self.__compare_init(next_step, 'name', [])

    def test_init_with_flags(self):
        flags = [Flag(action='Top Flag'), Flag(action='mod1_flag1')]
        expected_flag_json = [{'action': 'Top Flag', 'args': [], 'filters': []},
                              {'action': 'mod1_flag1', 'args': [], 'filters': []}]
        next_step = NextStep(name='name', flags=flags)
        self.__compare_init(next_step, 'name', expected_flag_json)

    def test_eq(self):
        flags = [Flag(action='mod1_flag1'), Flag(action='Top Flag')]
        next_steps = [NextStep(),
                      NextStep(name='name'),
                      NextStep(status='TestStatus'),
                      NextStep(name='name', flags=flags)]
        for i in range(len(next_steps)):
            for j in range(len(next_steps)):
                if i == j:
                    self.assertEqual(next_steps[i], next_steps[j])
                else:
                    self.assertNotEqual(next_steps[i], next_steps[j])

    def test_execute(self):
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
                self.assertEqual(next_step.execute(input_str, {}), expected_name)
            else:
                self.assertIsNone(next_step.execute(input_str, {}))
