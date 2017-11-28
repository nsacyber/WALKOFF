from collections import OrderedDict
from unittest import TestCase

from core.jsonelementcreator import JsonElementCreator


class Base(object):
    @classmethod
    def create(cls, json_in, reader=JsonElementCreator):
        return reader.create(json_in, element_class=cls)


class A(Base):
    def __init__(self, a, bs):
        Base.__init__(self)
        self.a = a
        self.bs = bs


class B(Base):
    def __init__(self, b, cs):
        Base.__init__(self)
        self.b = b
        self.cs = cs


class C(Base):
    def __init__(self, c, d):
        Base.__init__(self)
        self.c = c
        self.d = d


class D(Base):
    def __init__(self, d):
        Base.__init__(self)
        self.d = d


class TestJsonElementReader(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_class_order = JsonElementCreator.playbook_class_ordering

    def setUp(self):
        JsonElementCreator.playbook_class_ordering = OrderedDict([(A, {'bs': B}), (B, {'cs': C}), (C, None)])

    def tearDown(self):
        JsonElementCreator.playbook_class_ordering = self.original_class_order

    @classmethod
    def tearDownClass(cls):
        JsonElementCreator.playbook_class_ordering = cls.original_class_order

    def test_lowest(self):
        json_in = {'c': 'something', 'd': True}
        c = C.create(json_in)
        self.assertEqual(c.c, 'something')
        self.assertTrue(c.d)

    def test_lowest_invalid_json(self):
        json_in = {'invalid': 'something', 'd': True}
        with self.assertRaises(ValueError):
            C.create(json_in)

    def test_middle(self):
        json_in = {'b': 'something', 'cs': [{'c': 1, 'd': 2}, {'c': 2, 'd': 3}]}
        b = B.create(json_in)
        self.assertEqual(b.b, 'something')
        self.assertEqual(len(b.cs), 2)
        self.assertEqual(b.cs[0].c, 1)
        self.assertEqual(b.cs[0].d, 2)
        self.assertEqual(b.cs[1].c, 2)
        self.assertEqual(b.cs[1].d, 3)

    def test_middle_invalid_json(self):
        json_in = {'b': 'something', 'invalid': [{'c': 1, 'd': 2}, {'c': 2, 'd': 3}]}
        with self.assertRaises(ValueError):
            B.create(json_in)

    def test_top(self):
        json_in = {'a': 'top', 'bs': [{'b': 'something', 'cs': [{'c': 1, 'd': 2}, {'c': 2, 'd': 3}]},
                                      {'b': 'something2', 'cs': [{'c': 1, 'd': 2}, {'c': 2, 'd': 3}]},
                                      {'b': 'something3', 'cs': [{'c': 1, 'd': 2}, {'c': 2, 'd': 3}]}]}
        a = A.create(json_in)
        self.assertEqual(a.a, 'top')
        self.assertEqual(len(a.bs), 3)
        self.assertEqual(a.bs[0].b, 'something')
        self.assertEqual(a.bs[1].b, 'something2')
        self.assertEqual(a.bs[2].b, 'something3')

    def test_top_invalid_json(self):
        json_in = {'a': 'top', 'bs': [{'b': 'something', 'cs': [{'c': 1, 'd': 2}, {'c': 2, 'd': 3}]},
                                      {'b': 'something2', 'cs': [{'c': 1, 'd': 2}, {'c': 2, 'd': 3}]},
                                      {'b': 'something3', 'invalid': [{'c': 1, 'd': 2}, {'c': 2, 'd': 3}]}]}
        with self.assertRaises(ValueError):
            A.create(json_in)

    def test_multiple_in_class(self):
        JsonElementCreator.playbook_class_ordering = OrderedDict(
            [(A, {'bs': B}), (B, {'cs': C, 'b': D}), (C, None), (D, None)])
        json_in = {'b': [{'d': 1}, {'d': 3}], 'cs': [{'c': 1, 'd': 2}, {'c': 2, 'd': 3}]}
        b = B.create(json_in)
        self.assertEqual(len(b.cs), 2)
        self.assertEqual(b.cs[0].c, 1)
        self.assertEqual(b.cs[0].d, 2)
        self.assertEqual(b.cs[1].c, 2)
        self.assertEqual(b.cs[1].d, 3)
        self.assertEqual(len(b.b), 2)
        self.assertEqual(b.b[0].d, 1)
        self.assertEqual(b.b[1].d, 3)

    def test_invalid_class(self):
        class D(Base): pass

        json = {'a': 5, 'c': 45}
        with self.assertRaises(ValueError):
            D.create(json)
