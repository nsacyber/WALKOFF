import json
import unittest

from core import instance
from apps.HelloWorld import main

class TestUsersAndRoles(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testCreateInstance(self):

        inst = instance.Instance.create("HelloWorld", "testDevice")
        self.assertIsInstance(inst.instance, main.Main)
        self.assertEqual(inst.state, instance.OK)

    def testCall(self):

        inst = instance.Instance.create("HelloWorld", "testDevice")
        self.assertEqual(inst.instance, inst.__call__())

    def testShutdown(self):

        inst = instance.Instance.create("HelloWorld", "testDevice")
        self.assertEqual(inst.state, instance.OK)
        inst.shutdown()
        self.assertEqual(inst.state, instance.SHUTDOWN)
