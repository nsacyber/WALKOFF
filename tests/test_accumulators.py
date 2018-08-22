from unittest import TestCase
from walkoff.appgateway.accumulators import InMemoryAccumulator, ExternallyCachedAccumulator
from tests.util.mock_objects import MockRedisCacheAdapter
from uuid import uuid4


class TestInMemoryAccumulator(TestCase):

    def setUp(self):
        self.cache = InMemoryAccumulator()

    def test_init(self):
        self.assertIsInstance(self.cache, dict)

    def test_copy_raises(self):
        with self.assertRaises(AttributeError):
            self.cache.copy()

    def test_cmp_raises(self):
        cache2 = InMemoryAccumulator()
        with self.assertRaises(AttributeError):
            self.cache.__cmp__(cache2)

class TestExternallyCachedAccumulator(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.redis_cache = MockRedisCacheAdapter()


    def setUp(self):
        self.workflow_id = uuid4()
        self.cache = ExternallyCachedAccumulator(self.redis_cache, self.workflow_id)

    def test_setitem_getitem(self):
        self.cache['a'] = '42'
        self.assertEqual(self.cache['a'], '42')
        self.cache[42] = 'abc'
        self.assertEqual(self.cache[42], 'abc')

    def test_getitem_dne(self):
        with self.assertRaises(KeyError):
            self.cache['a']

    def test_len_empty(self):
        self.assertEqual(len(self.cache), 0)

    def test_len(self):
        self.cache['a'] = '1'
        self.cache['b'] = '2'
        self.cache['c'] = '3'
        self.assertEqual(len(self.cache), 3)

    def test_delitem(self):
        self.cache['a'] = '42'
        del self.cache['a']
        with self.assertRaises(KeyError):
            self.cache['a']

    def test_delitem_dne(self):
        with self.assertRaises(KeyError):
            del self.cache['a']

    def test_clear(self):
        self.cache['a'] = '1'
        self.cache['b'] = '2'
        self.cache['c'] = '3'
        self.cache.clear()
        for key in ('a', 'b', 'c'):
            with self.assertRaises(KeyError):
                self.cache[key]

    def test_has_key(self):
        self.assertFalse(self.cache.has_key('a'))
        self.cache['a'] = '3'
        self.assertTrue(self.cache.has_key('a'))

    def test_update(self):
        dict1 = {'a': '1', 'b': '2'}
        dict2 = {'c': '3'}
        dict3 = {'d': '4', 'e': '5'}
        self.cache['f'] = '6'
        self.cache.update(dict1, dict2, **dict3)
        for new_dict in (dict1, dict2, dict3):
            for key, value in new_dict.items():
                self.assertEqual(self.cache[key], value)
        self.assertEqual(self.cache['f'], '6')

    def test_keys(self):
        self.assertListEqual(list(self.cache.keys()), [])
        keys = {'a', 'b', 'c'}
        for i, key in enumerate(keys):
            self.cache[key] = i
        self.assertSetEqual({self.cache.extract_key(key) for key in self.cache.keys()}, keys)

    def test_values(self):
        self.assertListEqual(list(self.cache.values()), [])
        keys = ['a', 'b', 'c']
        for i, key in enumerate(keys):
            self.cache[key] = str(i)
        self.assertSetEqual(set(self.cache.values()), {str(i) for i in range(len(keys))})

    def test_items(self):
        self.assertListEqual(list(self.cache.items()), [])
        entries = {'a': '1', 'b': '2', 'c': '3'}
        self.cache.update(entries)
        retrieved = {self.cache.extract_key(key): value for key, value in self.cache.items()}
        self.assertEqual(len(retrieved), len(entries))
        #entries = {self.cache.format_key(key): value for key, value in entries.items()}
        #print(set(retrieved))
        #print(set(list(entries.items())))
        self.assertDictEqual(retrieved, entries)

    def test_pop_too_many_args(self):
        with self.assertRaises(TypeError):
            self.cache.pop(1, '2', '3')

    def test_pop(self):
        self.cache['a'] = '1'
        self.cache['b'] = '2'
        self.assertEqual(self.cache.pop('a', '2'), '1')

    def test_pop_with_default(self):
        self.cache['a'] = '1'
        self.cache['b'] = '2'
        self.assertEqual(self.cache.pop('c', '3'), '3')

    def test_pop_dne(self):
        with self.assertRaises(KeyError):
            self.cache.pop('a')

    def test_contains(self):
        self.assertFalse('a' in self.cache)
        self.cache['a'] = '3'
        self.assertTrue('a' in self.cache)

    def test_iter(self):
        keys = {'a', 'b', 'c'}
        for i, key in enumerate(keys):
            self.cache[key] = str(i)
        self.assertSetEqual({self.cache.extract_key(key) for key in self.cache}, keys)

    def test_format_key(self):
        self.assertEqual(
            self.cache.format_key('a'),
            '{0}{1}{2}{1}a'.format('accumulator', self.cache._cache_separator, self.workflow_id))