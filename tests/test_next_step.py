import unittest
import uuid

import apps
from core.case import callbacks
import core.config.config
from core.executionelements.condition import Condition
from core.executionelements.step import Step
from core.executionelements.nextstep import NextStep
from core.executionelements.workflow import Workflow
from core.decorators import ActionResult
from tests.config import test_apps_path


class TestNextStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def __compare_init(self, elem, source_uid, destination_uid, conditions=None, status='Success', uid=None, priority=999):
        self.assertEqual(elem.source_uid, source_uid)
        self.assertEqual(elem.destination_uid, destination_uid)
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
        next_step = NextStep(source_uid="1", destination_uid="2")
        self.__compare_init(next_step, "1", "2")

    def test_init_wth_uid(self):
        uid = uuid.uuid4().hex
        next_step = NextStep(source_uid="1", destination_uid="2", uid=uid)
        self.__compare_init(next_step, "1", "2", uid=uid)

    def test_init_with_status(self):
        next_step = NextStep(source_uid="1", destination_uid="2", status='test_status')
        self.__compare_init(next_step, "1", "2", status='test_status')

    def test_init_with_empty_conditions(self):
        next_step = NextStep(source_uid="1", destination_uid="2", conditions=[])
        self.__compare_init(next_step, '1', '2')

    def test_init_with_conditions(self):
        conditions = [Condition('HelloWorld', 'Top Condition'), Condition('HelloWorld', 'mod1_flag1')]
        expected_condition_json = [{'action': 'Top Condition', 'args': [], 'filters': []},
                              {'action': 'mod1_flag1', 'args': [], 'filters': []}]
        next_step = NextStep("1", "2", conditions=conditions)
        self.__compare_init(next_step, "1", "2", expected_condition_json)

    def test_eq(self):
        conditions = [Condition('HelloWorld', 'mod1_flag1'), Condition('HelloWorld', 'Top Condition')]
        next_steps = [NextStep(source_uid="1", destination_uid="2"),
                      NextStep(source_uid="1", destination_uid="2", status='TestStatus'),
                      NextStep(source_uid="1", destination_uid="2", conditions=conditions)]
        for i in range(len(next_steps)):
            for j in range(len(next_steps)):
                if i == j:
                    self.assertEqual(next_steps[i], next_steps[j])
                else:
                    self.assertNotEqual(next_steps[i], next_steps[j])

    def test_execute(self):
        conditions1 = [Condition('HelloWorld', 'regMatch', args={'regex': '(.*)'})]
        conditions2 = [Condition('HelloWorld', 'regMatch', args={'regex': '(.*)'}),
                       Condition('HelloWorld', 'regMatch', args={'regex': 'a'})]

        inputs = [('name1', [], ActionResult('aaaa', 'Success'), True),
                  ('name2', conditions1, ActionResult('anyString', 'Success'), True),
                  ('name3', conditions2, ActionResult('anyString', 'Success'), True),
                  ('name4', conditions2, ActionResult('bbbb', 'Success'), False),
                  ('name4', conditions2, ActionResult('aaaa', 'Custom'), False)]

        for name, conditions, input_str, expect_name in inputs:
            next_step = NextStep(source_uid="1", destination_uid="2", conditions=conditions)
            if expect_name:
                expected_name = next_step.destination_uid
                self.assertEqual(next_step.execute(input_str, {}), expected_name)
            else:
                self.assertIsNone(next_step.execute(input_str, {}))

    def test_get_next_step_no_next_steps(self):
        workflow = Workflow()
        self.assertIsNone(workflow.get_next_step(None, {}))

    def test_get_next_step_invalid_step(self):
        flag = Condition('HelloWorld', 'regMatch', args={'regex': 'aaa'})
        next_step = NextStep(source_uid="1", destination_uid='next', conditions=[flag])
        step = Step('HelloWorld', 'helloWorld', uid="2")
        step._output = ActionResult(result='bbb', status='Success')
        workflow = Workflow(steps=[step], next_steps=[next_step])
        self.assertIsNone(workflow.get_next_step(step, {}))

    def test_get_next_step(self):
        flag = Condition('HelloWorld', 'regMatch', args={'regex': 'aaa'})
        next_step = NextStep(source_uid="1", destination_uid="2", conditions=[flag])
        step = Step('HelloWorld', 'helloWorld', uid="1")
        step._output = ActionResult(result='aaa', status='Success')
        workflow = Workflow(steps=[step], next_steps=[next_step])

        result = {'triggered': False}

        @callbacks.data_sent.connect
        def validate_sent_data(sender, **kwargs):
            if isinstance(sender, NextStep):
                self.assertIn('callback_name', kwargs)
                self.assertEqual(kwargs['callback_name'], 'Next Step Taken')
                self.assertIn('object_type', kwargs)
                self.assertEqual(kwargs['object_type'], 'NextStep')
                result['triggered'] = True

        self.assertEqual(workflow.get_next_step(step, {}), '2')
        self.assertTrue(result['triggered'])

    def test_next_step_with_priority(self):
        flag = Condition('HelloWorld', 'regMatch', args={'regex': 'aaa'})
        next_step_one = NextStep(source_uid="1", destination_uid='five', conditions=[flag], priority="5")
        next_step_two = NextStep(source_uid="1", destination_uid='one', conditions=[flag], priority="1")
        step = Step('HelloWorld', 'helloWorld', uid="1")
        step._output = ActionResult(result='aaa', status='Success')
        workflow = Workflow(steps=[step], next_steps=[next_step_one, next_step_two])
        self.assertEqual(workflow.get_next_step(step, {}), "one")
