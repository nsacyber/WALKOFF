from walkoff.sse import StreamableBlueprint, SseStream
from walkoff.cache import RedisCacheAdapter
from unittest import TestCase
from mock import create_autospec


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
        blueprint.set_stream_caches(cache)
        for stream in blueprint.streams.values():
            self.assertEqual(stream.cache, cache)