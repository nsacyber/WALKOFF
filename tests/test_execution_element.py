import unittest
import uuid

from core.executionelement import ExecutionElement


class TestExecutionElement(unittest.TestCase):

    def test_init_default(self):
        elem = ExecutionElement()
        self.assertEqual(elem.name, '')
        self.assertIsNotNone(elem.uid)

    def test_init_with_name(self):
        elem = ExecutionElement(name='test')
        self.assertEqual(elem.name, 'test')
        self.assertIsNotNone(elem.uid)

    def test_init_with_uid(self):
        uid = uuid.uuid4().hex
        elem = ExecutionElement(uid=uid)
        self.assertEqual(elem.name, '')
        self.assertEqual(elem.uid, uid)