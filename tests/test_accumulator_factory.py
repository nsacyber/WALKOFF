from unittest import TestCase
from walkoff.appgateway.accumulators import *
from uuid import uuid4
from tests.config import TestConfig as Config
from walkoff.cache import make_cache

class MockWorkflow(object):

    def __init__(self):
        self.workflow_execution_id = uuid4()

    def get_execution_id(self):
        return self.workflow_execution_id

class TestAccumulatorFactory(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.workflow = MockWorkflow()

    def test_make_in_memory_accumulator(self):
        acc = make_in_memory_accumulator(Config, self.workflow)
        self.assertIsInstance(acc, InMemoryAccumulator)

    def test_make_external_accumulator(self):
        acc = make_external_accumulator(Config, self.workflow)
        self.assertIsInstance(acc, ExternallyCachedAccumulator)
        cache = make_cache(Config.CACHE)
        self.assertIs(acc._cache, cache)

    def test_make_accumulator_bad_config(self):
        class MockConfig(Config):
            ACCUMULATOR_TYPE = 'invalid'

        with self.assertRaises(ValueError):
            make_accumulator(self.workflow, MockConfig)


