import unittest
import uuid

from walkoff.core.executionelements.executionelement import ExecutionElement


class B(ExecutionElement):
    def __init__(self, b):
        ExecutionElement.__init__(self)
        self.b = b


class TestExecutionElement(unittest.TestCase):
    def assertAllNewUids(self, new_uids, original_uids):
        self.assertSetEqual(new_uids & original_uids, set())

    def test_init_default(self):
        elem = ExecutionElement()
        self.assertIsNotNone(elem.uid)

    def test_init_with_uid(self):
        uid = uuid.uuid4().hex
        elem = ExecutionElement(uid=uid)
        self.assertEqual(elem.uid, uid)

    def test_generate_new_uids_primitives_only(self):
        class A(ExecutionElement):
            def __init__(self):
                ExecutionElement.__init__(self)
                self.a = 42
                self.b = 'something'

        a = A()
        original_uid = a.uid
        a.regenerate_uids()
        self.assertNotEqual(a.uid, original_uid)

    def test_generate_new_uids_some_execution_elements(self):
        class A(ExecutionElement):
            def __init__(self):
                ExecutionElement.__init__(self)
                self.a = 42
                self.d = B('something')

        a = A()
        original_uid = a.uid
        original_d_uid = a.d.uid
        a.regenerate_uids()
        self.assertNotEqual(a.uid, original_uid)
        self.assertNotEqual(a.d.uid, original_d_uid)

    def test_generate_new_uids_list_execution_elements(self):
        class A(ExecutionElement):
            def __init__(self):
                ExecutionElement.__init__(self)
                self.a = 42
                self.d = [B(i) for i in range(3)]

        a = A()
        original_uid = a.uid
        original_d_uids = {d.uid for d in a.d}
        a.regenerate_uids()
        self.assertNotEqual(a.uid, original_uid)
        self.assertAllNewUids({d.uid for d in a.d}, original_d_uids)

    def test_generate_new_uids_dict_execution_elements(self):
        class A(ExecutionElement):
            def __init__(self):
                ExecutionElement.__init__(self)
                self.a = 42
                self.d = {i: B(i) for i in range(3)}

        a = A()
        original_uid = a.uid
        original_d_uids = {d.uid for d in a.d.values()}
        a.regenerate_uids()
        self.assertNotEqual(a.uid, original_uid)
        self.assertAllNewUids({d.uid for d in a.d.values()}, original_d_uids)

    def test_generate_new_uids_list_and_dict_and_value_execution_elements(self):
        class A(ExecutionElement):
            def __init__(self):
                ExecutionElement.__init__(self)
                self.a = 42
                self.b = B('a')
                self.c = [B(i) for i in range(3)]
                self.d = {i: B(i) for i in range(3)}

        a = A()
        original_uid = a.uid
        original_b_uid = a.b.uid
        original_c_uids = {c.uid for c in a.c}
        original_d_uids = {d.uid for d in a.d.values()}
        a.regenerate_uids()
        self.assertNotEqual(a.uid, original_uid)
        self.assertNotEqual(a.b.uid, original_b_uid)
        self.assertAllNewUids({c.uid for c in a.c}, original_c_uids)
        self.assertAllNewUids({d.uid for d in a.d.values()}, original_d_uids)
