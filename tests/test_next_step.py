import unittest
import uuid

import apps
import core.config.config
from core.decorators import ActionResult
from core.executionelements.condition import Condition
from core.executionelements.nextstep import NextStep
from core.helpers import import_all_transforms, import_all_conditions
from tests.config import test_apps_path, function_api_path


class TestNextStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.conditions = import_all_conditions('tests.util.conditionstransforms')
        core.config.config.transforms = import_all_transforms('tests.util.conditionstransforms')
        core.config.config.load_condition_transform_apis(path=function_api_path)

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def __compare_init(self, elem, src, dst, conditions=None, status='Success', uid=None, priority=float("inf")):
        self.assertEqual(elem.src, src)
        self.assertEqual(elem.dst, dst)
        self.assertEqual(elem.status, status)
        self.assertEqual(elem.priority, priority)
        if conditions:
            self.assertListEqual([condition.action for condition in elem.conditions],
                                 [condition['action'] for condition in conditions])
        if uid is None:
            self.assertIsNotNone(elem.uid)
        else:
            self.assertEqual(elem.uid, uid)

    def test_init(self):
        next_step = NextStep(src="1", dst="2")
        self.__compare_init(next_step, "1", "2")

    def test_init_wth_uid(self):
        uid = uuid.uuid4().hex
        next_step = NextStep(src="1", dst="2", uid=uid)
        self.__compare_init(next_step, "1", "2", uid=uid)

    def test_init_with_status(self):
        next_step = NextStep(src="1", dst="2", status='test_status')
        self.__compare_init(next_step, "1", "2", status='test_status')

    def test_init_with_empty_conditions(self):
        next_step = NextStep(src="1", dst="2", conditions=[])
        self.__compare_init(next_step, '1', '2')

    def test_init_with_conditions(self):
        conditions = [Condition(action='Top Condition'), Condition(action='mod1_flag1')]
        expected_condition_json = [{'action': 'Top Condition', 'args': [], 'filters': []},
                              {'action': 'mod1_flag1', 'args': [], 'filters': []}]
        next_step = NextStep("1", "2", conditions=conditions)
        self.__compare_init(next_step, "1", "2", expected_condition_json)

    def test_eq(self):
        conditions = [Condition(action='mod1_flag1'), Condition(action='Top Condition')]
        next_steps = [NextStep(src="1", dst="2"),
                      NextStep(src="1", dst="2", status='TestStatus'),
                      NextStep(src="1", dst="2", conditions=conditions)]
        for i in range(len(next_steps)):
            for j in range(len(next_steps)):
                if i == j:
                    self.assertEqual(next_steps[i], next_steps[j])
                else:
                    self.assertNotEqual(next_steps[i], next_steps[j])

    def test_execute(self):
        conditions1 = [Condition(action='regMatch', args={'regex': '(.*)'})]
        conditions2 = [Condition(action='regMatch', args={'regex': '(.*)'}),
                  Condition(action='regMatch', args={'regex': 'a'})]

        inputs = [('name1', [], ActionResult('aaaa', 'Success'), True),
                  ('name2', conditions1, ActionResult('anyString', 'Success'), True),
                  ('name3', conditions2, ActionResult('anyString', 'Success'), True),
                  ('name4', conditions2, ActionResult('bbbb', 'Success'), False),
                  ('name4', conditions2, ActionResult('aaaa', 'Custom'), False)]

        for name, conditions, input_str, expect_name in inputs:
            next_step = NextStep(src="1", dst="2", conditions=conditions)
            if expect_name:
                expected_name = next_step.dst
                self.assertEqual(next_step.execute(input_str, {}), expected_name)
            else:
                self.assertIsNone(next_step.execute(input_str, {}))
