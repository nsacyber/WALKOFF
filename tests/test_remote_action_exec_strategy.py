from unittest import TestCase
from uuid import uuid4

import requests_mock

from walkoff.helpers import ExecutionError
from walkoff.worker.action_exec_strategy import RemoteActionExecutionStrategy, ExecutableContext


class MockWorkflowExecContext(object):
    id = str(uuid4())
    execution_id = str(uuid4())
    name = 'test'


class TestRemoteActionExecStrategy(TestCase):

    def setUp(self):
        self.strategy = RemoteActionExecutionStrategy(MockWorkflowExecContext)

    @staticmethod
    def make_execution_context(
            executable_type='action',
            app_name='HelloWorld',
            executable_name='test',
            executable_id=None,
            execution_id=None
    ):
        if not execution_id:
            execution_id = uuid4()
        if not executable_id:
            executable_id = uuid4()
        return ExecutableContext(executable_type, app_name, executable_name, executable_id, execution_id=execution_id)

    def test_404_error_non_action(self):
        execution_id = str(uuid4())
        context = self.make_execution_context(execution_id=execution_id, executable_type='condition')
        url = RemoteActionExecutionStrategy.format_url('HelloWorld', MockWorkflowExecContext.execution_id, execution_id)

        acc = {}
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=404, json={'title': 'Nothing found'})
            with self.assertRaises(ExecutionError):
                self.strategy.execute_from_context(context, acc, {})

    def test_404_error_action(self):
        execution_id = str(uuid4())
        context = self.make_execution_context(execution_id=execution_id)
        url = RemoteActionExecutionStrategy.format_url('HelloWorld', MockWorkflowExecContext.execution_id, execution_id)

        acc = {}
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=404, json={'title': 'Nothing found'})
            result = self.strategy.execute_from_context(context, acc, {})
            self.assertEqual(result.status, 'UnhandledException')
            self.assertIsNone(result.result)

    def test_unhandled_exception_non_action(self):
        execution_id = str(uuid4())
        context = self.make_execution_context(execution_id=execution_id, executable_type='condition')
        url = RemoteActionExecutionStrategy.format_url('HelloWorld', MockWorkflowExecContext.execution_id, execution_id)

        acc = {}
        condition_result = 'Some error message'
        acc[str(context.id)] = condition_result
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=200, json={'status': 'UnhandledException', 'result_key': str(uuid4())})
            with self.assertRaises(ExecutionError):
                self.strategy.execute_from_context(context, acc, {})

    def test_unhandled_exception_action(self):
        execution_id = str(uuid4())
        context = self.make_execution_context(execution_id=execution_id)
        url = RemoteActionExecutionStrategy.format_url('HelloWorld', MockWorkflowExecContext.execution_id, execution_id)

        acc = {}
        action_result = 'Some error message'
        acc[str(context.id)] = action_result
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=200, json={'status': 'UnhandledException', 'result_key': str(uuid4())})
            result = self.strategy.execute_from_context(context, acc, {})
            self.assertEqual(result.status, 'UnhandledException')
            self.assertIsNone(result.result)

    def test_execute_non_action(self):
        execution_id = str(uuid4())
        context = self.make_execution_context(execution_id=execution_id, executable_type='condition')
        url = RemoteActionExecutionStrategy.format_url('HelloWorld', MockWorkflowExecContext.execution_id, execution_id)

        acc = {}
        condition_result = 'Some error message'
        acc[str(context.id)] = condition_result
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=200, json={'status': 'Success', 'result_key': str(uuid4())})
            result = self.strategy.execute_from_context(context, acc, {})
            self.assertEqual(result, condition_result)

    def test_execute_action(self):
        execution_id = str(uuid4())
        context = self.make_execution_context(execution_id=execution_id)
        url = RemoteActionExecutionStrategy.format_url('HelloWorld', MockWorkflowExecContext.execution_id, execution_id)

        acc = {}
        action_result = 'Some error message'
        acc[str(context.id)] = action_result
        with requests_mock.Mocker() as mocker:
            mocker.post(url, status_code=200, json={'status': 'CustomSuccess', 'result_key': str(uuid4())})
            result = self.strategy.execute_from_context(context, acc, {})
            self.assertEqual(result.status, 'CustomSuccess')
            self.assertIsNone(result.result)
