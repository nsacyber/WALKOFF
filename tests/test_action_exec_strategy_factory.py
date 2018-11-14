from unittest import TestCase
from uuid import uuid4

from walkoff.worker.action_exec_strategy import LocalActionExecutionStrategy, make_execution_strategy, \
    RemoteActionExecutionStrategy


class MockRestrictedWorkflowContext:
    id = str(uuid4())
    execution_id = str(uuid4())
    name = 'test'


class TestActionExecutionStrategyFactory(TestCase):

    def test_local_strategy_creation(self):
        class MockConfig:
            ACTION_EXECUTION_STRATEGY = 'local'

        self.assertIsInstance(
            make_execution_strategy(MockConfig, MockRestrictedWorkflowContext),
            LocalActionExecutionStrategy
        )

    def test_remote_strategy_creation(self):
        class MockConfig:
            ACTION_EXECUTION_STRATEGY = 'remote'

        self.assertIsInstance(
            make_execution_strategy(MockConfig, MockRestrictedWorkflowContext),
            RemoteActionExecutionStrategy
        )

    def test_unknown_strategy_creation(self):
        class MockConfig:
            ACTION_EXECUTION_STRATEGY = 'invalid'

        with self.assertRaises(ValueError):
            make_execution_strategy(MockConfig, MockRestrictedWorkflowContext)
