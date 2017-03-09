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
        xml_string = elementtree.tostring(options_xml)
        expected_xml = \
            b'<options><enabled>true</enabled><scheduler autorun="true" type="test_type"><arg1>val1</arg1><arg2>val2</arg2><arg3>val3</arg3></scheduler></options>'
        self.assertEqual(xml_string, expected_xml)
        options_derived = Options(xml=ElementTree.fromstring(xml_string))
        self.assertEqual(options.enabled, options_derived.enabled)
        self.assertEqual(options.scheduler['type'], options_derived.scheduler['type'])
        self.assertEqual(options.scheduler['autorun'], options_derived.scheduler['autorun'])
        self.assertDictEqual(options.scheduler['args'], options_derived.scheduler['args'])
