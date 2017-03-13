import unittest
import xml.etree.cElementTree as elementtree
from xml.etree import ElementTree
from core.options import Options


class TestWorkflowOptions(unittest.TestCase):

    def test_to_xml(self):
        expected_args = {"arg1": "val1", "arg2": "val2", "arg3": "val3"}
        scheduler = {'type': 'test_type',
                     'autorun': 'true',
                     'args': expected_args}
        options = Options(enabled=True, scheduler=scheduler)
        options_xml = options.to_xml()
        options_derived = Options(xml=options_xml)
        self.assertEqual(options.enabled, options_derived.enabled)
        self.assertEqual(options.scheduler['type'], options_derived.scheduler['type'])
        self.assertEqual(options.scheduler['autorun'], options_derived.scheduler['autorun'])
        self.assertDictEqual(options.scheduler['args'], options_derived.scheduler['args'])

    def test_as_json(self):
        expected_args = {"arg1": "val1", "arg2": "val2", "arg3": "val3"}
        scheduler = {'type': 'test_type',
                     'autorun': 'true',
                     'args': expected_args}
        options = Options(enabled=True, scheduler=scheduler)
        expected_json = {'enabled': 'True',
                         'children': {},
                         'scheduler': scheduler}
        self.assertDictEqual(options.as_json(), expected_json)
