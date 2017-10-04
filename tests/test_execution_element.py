import unittest
import uuid

from core.executionelement import ExecutionElement


class TestExecutionElement(unittest.TestCase):

    def test_init_default(self):
        elem = ExecutionElement()
        self.assertIsNotNone(elem.uid)

    def test_init_with_uid(self):
        uid = uuid.uuid4().hex
        elem = ExecutionElement(uid=uid)
        self.assertEqual(elem.uid, uid)
