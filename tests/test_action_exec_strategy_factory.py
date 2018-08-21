from unittest import TestCase
from walkoff.worker.action_exec_strategy import LocalActionExecutionStrategy, make_execution_strategy


class TestActionExecutionStrategyFactory(TestCase):

    def test_local_strategy_creation(self):
        class MockConfig:
            ACTION_EXECUTION_STRATEGY = 'local'

        self.assertIsInstance(make_execution_strategy(MockConfig), LocalActionExecutionStrategy)

    def test_unknown_strategy_creation(self):
        class MockConfig:
            ACTION_EXECUTION_STRATEGY = 'invalid'

        with self.assertRaises(ValueError):
            make_execution_strategy(MockConfig)


