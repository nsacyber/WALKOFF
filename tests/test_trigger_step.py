import unittest

from core.executionelements.flag import Flag
from core.case.callbacks import data_sent
import core.config.config
import core.config.paths
from core.executionelements.triggerstep import TriggerStep
from core.executionelements.step import Step
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

    def test_execute_generates_execution_uid(self):
        step = TriggerStep()
        original_execution_uid = step.get_execution_uid()
        step.execute(None, {})
        self.assertNotEqual(step.get_execution_uid(), original_execution_uid)

    def test_execute_with_flags(self):
        flags = [Flag(action='regMatch', args={'regex': 'aaa'})]
        step = TriggerStep(flags=flags)
        self.assertTrue(step.execute('aaa', {}))

    def test_execute_with_flags_sends_callbacks(self):
        flags = [Flag(action='regMatch', args={'regex': 'aaa'})]
        step = TriggerStep(flags=flags)

        result = {'triggered': False}

        @data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, TriggerStep):
                self.assertIs(sender, step)
                self.assertIn('callback_name', kwargs)
                self.assertEqual(kwargs['callback_name'], 'Trigger Step Taken')
                self.assertIn('object_type', kwargs)
                self.assertEqual(kwargs['object_type'], 'Step')
                result['triggered'] = True

        step.execute('aaa', {})
        self.assertTrue(result['triggered'])

    def test_execute_with_flags_failed(self):
        flags = [Flag(action='regMatch', args={'regex': 'aaa'})]
        step = TriggerStep(flags=flags)
        self.assertFalse(step.execute('bbb', {}))

    def test_execute_with_flags__failed_sends_callbacks(self):
        flags = [Flag(action='regMatch', args={'regex': 'aaa'})]
        step = TriggerStep(flags=flags)

        result = {'triggered': False}

        @data_sent.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, TriggerStep):
                self.assertIs(sender, step)
                self.assertIn('callback_name', kwargs)
                self.assertEqual(kwargs['callback_name'], 'Trigger Step Not Taken')
                self.assertIn('object_type', kwargs)
                self.assertEqual(kwargs['object_type'], 'Step')
                result['triggered'] = True

        step.execute('bbb', {})
        self.assertTrue(result['triggered'])
