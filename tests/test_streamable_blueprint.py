from unittest import TestCase

from mock import create_autospec

from walkoff.cache import RedisCacheAdapter
from walkoff.sse import StreamableBlueprint, SseStream


class TestStreamableBlueprint(TestCase):

    def test_init(self):
        stream1 = SseStream('name1')
        stream2 = SseStream('name2')
        blueprint = StreamableBlueprint(
            'custom_interface',
            'interfaces',
            streams=(stream1, stream2))
        self.assertEqual(blueprint.name, 'custom_interface')
        self.assertEqual(blueprint.import_name, 'interfaces')
        self.assertDictEqual(blueprint.streams, {'name1': stream1, 'name2': stream2})
        self.assertIsNone(blueprint.cache)

    def test_init_no_streams(self):
        blueprint = StreamableBlueprint(
            'custom_interface',
            'interfaces')
        self.assertEqual(blueprint.name, 'custom_interface')
        self.assertEqual(blueprint.import_name, 'interfaces')
        self.assertDictEqual(blueprint.streams, {})

    def test_set_caches(self):
        stream1 = SseStream('name1')
        stream2 = SseStream('name2')
        for stream in (stream1, stream2):
            stream.cache = None
        blueprint = StreamableBlueprint(
            'custom_interface',
            'interfaces',
            streams=(stream1, stream2))
        cache = create_autospec(RedisCacheAdapter)
        blueprint.cache = cache
        for stream in blueprint.streams.values():
            self.assertEqual(stream.cache, cache)
        self.assertEqual(blueprint.cache, cache)

    def test_set_caches_some_not_none(self):
        class MockCache: pass

        cache2 = MockCache()
        stream1 = SseStream('name1')
        stream2 = SseStream('name2', cache=cache2)
        stream1.cache = None
        blueprint = StreamableBlueprint(
            'custom_interface',
            'interfaces',
            streams=(stream1, stream2))
        cache = create_autospec(RedisCacheAdapter)
        blueprint.cache = cache
        self.assertEqual(stream1.cache, cache)
        self.assertEqual(stream2.cache, cache2)
        self.assertEqual(blueprint.cache, cache)
