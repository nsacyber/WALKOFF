import unittest
from core.nextstep import NextStep
from core.flag import Flag
from core.helpers import import_all_filters, import_all_flags, import_all_apps
from tests.config import test_apps_path, function_api_path
import core.config.config
from tests.apps import App
from core.decorators import ActionResult
import uuid


class TestNextStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        App.registry = {}
        import_all_apps(path=test_apps_path, reload=True)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

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

    def test_as_json(self):
        uid = uuid.uuid4().hex
        self.assertDictEqual(NextStep(uid=uid).as_json(), {'name': '', 'status': 'Success', 'flags': [], 'uid': uid})

    def test_as_json_with_name(self):
        uid = uuid.uuid4().hex
        self.assertDictEqual(NextStep(name='name1', uid=uid).as_json(),
                             {'name': 'name1', 'status': 'Success', 'flags': [], 'uid': uid})

    def test_as_json_with_status(self):
        uid = uuid.uuid4().hex
        self.assertDictEqual(NextStep(status='test_status', uid=uid).as_json(),
                             {'name': '', 'status': 'test_status', 'flags': [], 'uid': uid})

    def test_as_json_full(self):
        uid = uuid.uuid4().hex
        flags = [Flag(action='Top Flag', uid=uid), Flag(action='mod1_flag1', uid=uid)]
        expected_flag_json = [{'action': 'Top Flag', 'args': [], 'filters': [], 'uid': uid},
                              {'action': 'mod1_flag1', 'args': [], 'filters': [], 'uid': uid}]
        self.assertDictEqual(NextStep(name='name1', flags=flags, uid=uid).as_json(),
                             {'name': 'name1', 'status': 'Success', 'flags': expected_flag_json, 'uid': uid})

    def test_from_json_name_only(self):
        json_in = {'name': 'name1', 'flags': []}
        next_step = NextStep.from_json(json_in)
        self.__compare_init(next_step, 'name1', [])

    def test_from_json_with_status(self):
        json_in = {'name': 'name1', 'status': 'test_status', 'flags': []}
        next_step = NextStep.from_json(json_in)
        self.__compare_init(next_step, 'name1', [], status='test_status')

    def test_from_json_with_flags(self):
        flag_json = [{'action': 'Top Flag', 'args': [], 'filters': []},
                     {'action': 'mod1_flag1', 'args': [], 'filters': []}]
        next_step = NextStep.from_json({'name': 'name1', 'flags': flag_json})
        self.__compare_init(next_step, 'name1', flag_json)

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
