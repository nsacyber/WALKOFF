import unittest
import socket
from core.flag import Flag
from core.triggerstep import TriggerStep, _Widget
from core.decorators import ActionResult
import core.config.config
import core.config.paths
from tests.config import test_apps_path, function_api_path
from core.instance import Instance
from core.helpers import (import_all_apps, UnknownApp, UnknownAppAction, InvalidInput, import_all_flags,
                          import_all_filters, InvalidElementConstructed)
import uuid


class TestStepTrigger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_apps(path=test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def setUp(self):
        self.uid = uuid.uuid4().hex
        self.basic_json = {'action': 'helloWorld',
                           'name': '',
                           'flags': [],
                           'status': 'Success',
                           'position': {},
                           'widgets': [],
                           'uid': self.uid}
        self.basic_input_json = {'action': 'helloWorld',
                                 'name': '',
                                 'flags': [],
                                 'status': 'Success',
                                 'position': {},
                                 'uid': self.uid}

    def __compare_init(self, elem, name, action, flags, widgets, status='Success', position=None, uid=None):
        self.assertEqual(elem.name, name)
        self.assertEqual(elem.action, action)
        self.assertListEqual([flag.action for flag in elem.flags], [flag['action'] for flag in flags])
        self.assertEqual(elem.status, status)
        widgets = [_Widget(app, widget) for (app, widget) in widgets]
        self.assertEqual(len(elem.widgets), len(widgets))
        for widget in elem.widgets:
            self.assertIn(widget, widgets)
        position = position if position is not None else {}
        self.assertDictEqual(elem.position, position)
        self.assertIsNone(elem.output)
        self.assertFalse(elem.templated)
        if uid is None:
            self.assertIsNotNone(elem.uid)
        else:
            self.assertEqual(elem.uid, uid)

    def test_init_action_only(self):
        step = TriggerStep(action='helloWorld')
        self.__compare_init(step, '', 'helloWorld', [], [])

    def test_init_with_name(self):
        step = TriggerStep(action='helloWorld', name='name')
        self.__compare_init(step, 'name', 'helloWorld', [], [])

    def test_init_with_empty_flags(self):
        step = TriggerStep(action='helloWorld', name='name', flags=[])
        self.__compare_init(step, 'name', 'helloWorld', [], [])

    def test_init_with_flags(self):
        flags = [Flag(action='Top Flag'), Flag(action='mod1_flag1')]
        expected_flag_json = [{'action': 'Top Flag', 'args': [], 'filters': []},
                              {'action': 'mod1_flag1', 'args': [], 'filters': []}]
        step = TriggerStep(action='helloWorld', name='name', flags=flags)
        self.__compare_init(step, 'name', 'helloWorld', expected_flag_json, [])

    def test_init_with_status(self):
        step = TriggerStep(action='helloWorld', status='test_status')
        self.__compare_init(step, '', 'helloWorld', [], [], status='test_status')

    def test_init_with_position(self):
        step = TriggerStep(action='helloWorld', position={'x': -12.3, 'y': 485})
        self.__compare_init(step, '', 'helloWorld', [], [], position={'x': -12.3, 'y': 485})

    def test_init_with_widgets(self):
        widgets = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        step = TriggerStep(action='helloWorld', widgets=widgets)
        self.__compare_init(step, '', 'helloWorld', [], widgets)

    def test_init_with_uid(self):
        uid = uuid.uuid4().hex
        step = TriggerStep(action='helloWorld', uid=uid)
        self.__compare_init(step, '', 'helloWorld', [], [], uid=uid)

    def test_as_json(self):
        step = TriggerStep(action='helloWorld', uid=self.uid)
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_name(self):
        step = TriggerStep(action='helloWorld', name='name', uid=self.uid)
        self.basic_json['name'] = 'name'
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_flags(self):
        flags = [Flag(action='Top Flag'), Flag(action='mod1_flag1')]
        step = TriggerStep(action='helloWorld', flags=flags, uid=self.uid)
        self.basic_json['flags'] = [flag.as_json() for flag in flags]
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_status(self):
        step = TriggerStep(action='helloWorld', status='test_status', uid=self.uid)
        self.basic_json['status'] = 'test_status'
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_position(self):
        step = TriggerStep(action='helloWorld', position={'x': -12.3, 'y': 485}, uid=self.uid)
        self.basic_json['position'] = {'x': -12.3, 'y': 485}
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_as_json_with_widgets(self):
        widgets = [('aaa', 'bbb'), ('ccc', 'ddd'), ('eee', 'fff')]
        step = TriggerStep(action='helloWorld', widgets=widgets, uid=self.uid)
        self.basic_json['widgets'] = [{'app': widget[0], 'name': widget[1]} for widget in widgets]
        self.assertDictEqual(step.as_json(), self.basic_json)

    def test_from_json_with_name(self):
        self.basic_input_json['name'] = 'name'
        step = TriggerStep.from_json(self.basic_input_json, {})
        self.__compare_init(step, 'name', 'helloWorld', [], [])

    def test_from_json_with_flags(self):
        flag_json = [{'action': 'Top Flag', 'args': [], 'filters': []},
                     {'action': 'mod1_flag1', 'args': [], 'filters': []}]
        self.basic_input_json['flags'] = flag_json
        step = TriggerStep.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', flag_json, [])

    def test_from_json_with_status(self):
        self.basic_input_json['status'] = 'test_status'
        step = TriggerStep.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', [], [], status='test_status')

    def test_from_json_with_position(self):
        step = TriggerStep.from_json(self.basic_input_json, {'x': 125.3, 'y': 198.7})
        self.__compare_init(step, '', 'helloWorld', [], [], position={'x': 125.3, 'y': 198.7})

    def test_from_json_with_widgets(self):
        widget_json = [{'name': 'widget_name', 'app': 'app1'}, {'name': 'w2', 'app': 'app2'}]
        widget_tuples = [('app1', 'widget_name'), ('app2', 'w2')]
        self.basic_input_json['widgets'] = widget_json
        step = TriggerStep.from_json(self.basic_input_json, {})
        self.__compare_init(step, '', 'helloWorld', [], widget_tuples)

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
            step = TriggerStep(action='helloWorld', flags=flags)
            if expect_name:
                expected_name = step.name
                self.assertEqual(step(input_str, {}), expected_name)
            else:
                self.assertIsNone(step(input_str, {}))
