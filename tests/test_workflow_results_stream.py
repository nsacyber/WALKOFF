from tests.util.mock_objects import MockRedisCacheAdapter
from walkoff.server.blueprints.workflowresults import *
from walkoff.executiondb import ActionStatusEnum, WorkflowStatusEnum
from uuid import uuid4
import json
from mock import patch
from copy import deepcopy
from tests.util.servertestcase import ServerTestCase
from walkoff.executiondb.workflowresults import WorkflowStatus, ActionStatus
from flask import Response
from walkoff.server.returncodes import SUCCESS


class TestWorkflowResultsStream(ServerTestCase):

    def setUp(self):
        self.cache = MockRedisCacheAdapter()
        workflow_stream.cache = self.cache
        action_stream.cache = self.cache

    def tearDown(self):
        self.cache.clear()
        for status in self.app.running_context.execution_db.session.query(WorkflowStatus).all():
            self.app.running_context.execution_db.session.delete(status)
        self.app.running_context.execution_db.session.commit()

    def assert_and_strip_timestamp(self, data, field='timestamp'):
        timestamp = data.pop(field, None)
        self.assertIsNotNone(timestamp)

    @staticmethod
    def get_sample_action_sender():
        argument_id = str(uuid4())
        action_id = str(uuid4())
        action_execution_id = str(uuid4())
        arguments = [{'name': 'a', 'value': '42'},
                     {'name': 'b', 'reference': argument_id, 'selection': json.dumps(['a', '1'])}]
        return {
            'action_name': 'some_action_name',
            'app_name': 'HelloWorld',
            'id': action_id,
            'name': 'my_name',
            'execution_id': action_execution_id,
            'arguments': arguments
        }

    @staticmethod
    def get_action_kwargs(with_result=False):
        workflow_id = str(uuid4())
        ret = {'workflow': {'execution_id': workflow_id}}
        if with_result:
            ret['data'] = {'result': 'some result'}
        return ret

    def test_format_action_data(self):
        workflow_id = str(uuid4())
        kwargs = {'data': {'workflow': {'execution_id': workflow_id}}}
        sender = self.get_sample_action_sender()
        status = ActionStatusEnum.executing
        result = format_action_data(sender, kwargs, status)
        expected = sender
        expected['action_id'] = expected.pop('id')
        expected['workflow_execution_id'] = workflow_id
        expected['status'] = status.name
        self.assert_and_strip_timestamp(result)
        self.assertDictEqual(result, expected)

    def test_format_action_data_with_results(self):
        workflow_id = str(uuid4())
        kwargs = {'data': {'workflow': {'execution_id': workflow_id},
                           'data': {'result': 'some result'}}}
        sender = self.get_sample_action_sender()
        status = ActionStatusEnum.executing
        result = format_action_data_with_results(sender, kwargs, status)
        expected = sender
        expected['action_id'] = expected.pop('id')
        expected['workflow_execution_id'] = workflow_id
        expected['status'] = status.name
        expected['result'] = 'some result'
        self.assert_and_strip_timestamp(result)
        self.assertDictEqual(result, expected)

    def check_action_callback(self, callback, status, event, mock_publish, with_result=False):
        sender = self.get_sample_action_sender()
        kwargs = self.get_action_kwargs(with_result=with_result)
        if not with_result:
            expected = format_action_data(deepcopy(sender), {'data': kwargs}, status)
        else:
            expected = format_action_data_with_results(deepcopy(sender), {'data': kwargs}, status)
        expected.pop('timestamp')
        callback(sender, data=kwargs)
        mock_publish.assert_called_once()
        mock_publish.call_args[0][0].pop('timestamp')
        mock_publish.assert_called_with(expected, event=event)

    @patch.object(action_stream, 'publish')
    def test_action_started_callback(self, mock_publish):
        self.check_action_callback(action_started_callback, ActionStatusEnum.executing, 'started', mock_publish)

    @patch.object(action_stream, 'publish')
    def test_action_ended_callback(self, mock_publish):
        self.check_action_callback(
            action_ended_callback,
            ActionStatusEnum.success,
            'success',
            mock_publish,
            with_result=True)

    @patch.object(action_stream, 'publish')
    def test_action_error_callback(self, mock_publish):
        self.check_action_callback(
            action_error_callback,
            ActionStatusEnum.failure,
            'failure', mock_publish,
            with_result=True)

    @patch.object(action_stream, 'publish')
    def test_action_args_invalid_callback(self, mock_publish):
        self.check_action_callback(
            action_args_invalid_callback,
            ActionStatusEnum.failure,
            'failure',
            mock_publish,
            with_result=True)

    @patch.object(action_stream, 'publish')
    def test_trigger_waiting_data_action_callback(self, mock_publish):
        self.check_action_callback(
            trigger_awaiting_data_action_callback,
            ActionStatusEnum.awaiting_data,
            'awaiting_data',
            mock_publish)

    @staticmethod
    def get_workflow_sender(execution_id=None):
        execution_id = execution_id or str(uuid4())
        workflow_id = str(uuid4())
        return {'execution_id': execution_id, 'id': workflow_id, 'name': 'workflow1'}

    def test_format_workflow_result(self):
        execution_id = str(uuid4())
        workflow_id = str(uuid4())
        sender = {'execution_id': execution_id, 'id': workflow_id, 'name': 'workflow1'}
        result = format_workflow_result(sender, WorkflowStatusEnum.pending)
        self.assert_and_strip_timestamp(result)
        sender['workflow_id'] = sender.pop('id')
        sender['status'] = WorkflowStatusEnum.pending.name
        self.assertDictEqual(result, sender)

    def get_workflow_status(self, workflow_execution_id, status):
        workflow_id = uuid4()
        workflow_status = WorkflowStatus(workflow_execution_id, workflow_id, 'workflow1')
        action_execution_id = uuid4()
        action_id = uuid4()
        self.app.running_context.execution_db.session.add(workflow_status)
        action_status = ActionStatus(action_execution_id, action_id, 'my action', 'the_app', 'the_action')
        self.app.running_context.execution_db.session.add(action_status)
        workflow_status.add_action_status(action_status)
        expected = {
            'execution_id': str(workflow_execution_id),
            'workflow_id': str(workflow_id),
            'name': 'workflow1',
            'status': status.name,
            'current_action': action_status.as_json(summary=True)}
        return expected, workflow_status

    def test_format_workflow_result_with_current_step(self):
        workflow_execution_id = uuid4()
        expected, _ = self.get_workflow_status(workflow_execution_id, WorkflowStatusEnum.running)

        result = format_workflow_result_with_current_step(workflow_execution_id, WorkflowStatusEnum.running)
        self.assert_and_strip_timestamp(result)
        self.assertDictEqual(result, expected)

    def test_format_workflow_result_with_current_step_mismatched_status(self):
        workflow_execution_id = uuid4()
        expected, status = self.get_workflow_status(workflow_execution_id, WorkflowStatusEnum.running)
        status.paused()
        result = format_workflow_result_with_current_step(workflow_execution_id, WorkflowStatusEnum.running)
        self.assert_and_strip_timestamp(result)
        self.assertDictEqual(result, expected)

    def test_format_workflow_result_with_current_step_no_result_found(self):
        workflow_execution_id = uuid4()
        expected = {'execution_id': str(workflow_execution_id), 'status': WorkflowStatusEnum.paused.name}
        result = format_workflow_result_with_current_step(workflow_execution_id, WorkflowStatusEnum.paused)
        self.assert_and_strip_timestamp(result)
        self.assertDictEqual(result, expected)

    def check_workflow_callback(self, callback, sender, status, event, mock_publish, expected=None, **kwargs):
        if not expected:
            expected = format_workflow_result(deepcopy(sender), status)
            expected.pop('timestamp')
        callback(sender, **kwargs)
        mock_publish.assert_called_once()
        self.assert_and_strip_timestamp(mock_publish.call_args[0][0])
        mock_publish.assert_called_with(expected, event=event)

    @patch.object(workflow_stream, 'publish')
    def test_workflow_pending_callback(self, mock_publish):
        sender = self.get_workflow_sender()
        self.check_workflow_callback(
            workflow_pending_callback,
            sender,
            WorkflowStatusEnum.pending,
            'queued',
            mock_publish)

    @patch.object(workflow_stream, 'publish')
    def test_workflow_started_callback(self, mock_publish):
        sender = self.get_workflow_sender()
        self.check_workflow_callback(
            workflow_started_callback,
            sender,
            WorkflowStatusEnum.running,
            'started',
            mock_publish)

    @patch.object(workflow_stream, 'publish')
    def test_workflow_paused_callback(self, mock_publish):
        workflow_execution_id = uuid4()
        sender = self.get_workflow_sender(execution_id=str(workflow_execution_id))
        expected, status = self.get_workflow_status(workflow_execution_id, WorkflowStatusEnum.paused)
        self.check_workflow_callback(
            workflow_paused_callback,
            sender,
            WorkflowStatusEnum.paused,
            'paused',
            mock_publish,
            expected=expected)

    @patch.object(workflow_stream, 'publish')
    def test_workflow_resumed_callback(self, mock_publish):
        workflow_execution_id = uuid4()

        class MockWorkflowSender(object):
            def get_execution_id(self):
                return workflow_execution_id

        sender = MockWorkflowSender()
        expected, status = self.get_workflow_status(workflow_execution_id, WorkflowStatusEnum.running)
        self.check_workflow_callback(
            workflow_resumed_callback,
            sender,
            WorkflowStatusEnum.running,
            'resumed',
            mock_publish,
            expected=expected)

    @patch.object(workflow_stream, 'publish')
    def test_trigger_awaiting_data_workflow_callback(self, mock_publish):
        workflow_execution_id = uuid4()
        expected, status = self.get_workflow_status(workflow_execution_id, WorkflowStatusEnum.awaiting_data)
        self.check_workflow_callback(
            trigger_awaiting_data_workflow_callback,
            None,
            WorkflowStatusEnum.awaiting_data,
            'awaiting_data',
            mock_publish,
            expected=expected,
            data={'workflow': {'execution_id': str(workflow_execution_id)}})

    @patch.object(workflow_stream, 'publish')
    def test_trigger_action_taken_callback(self, mock_publish):
        workflow_execution_id = uuid4()
        expected, status = self.get_workflow_status(workflow_execution_id, WorkflowStatusEnum.pending)
        self.check_workflow_callback(
            trigger_action_taken_callback,
            None,
            WorkflowStatusEnum.pending,
            'triggered',
            mock_publish,
            expected=expected,
            data={'workflow_execution_id': str(workflow_execution_id)})

    @patch.object(workflow_stream, 'publish')
    def test_workflow_aborted_callback(self, mock_publish):
        sender = self.get_workflow_sender()
        self.check_workflow_callback(
            workflow_aborted_callback,
            sender,
            WorkflowStatusEnum.aborted,
            'aborted',
            mock_publish)

    @patch.object(workflow_stream, 'publish')
    def test_workflow_shutdown_callback(self, mock_publish):
        sender = self.get_workflow_sender()
        self.check_workflow_callback(
            workflow_shutdown_callback,
            sender,
            WorkflowStatusEnum.completed,
            'completed',
            mock_publish)

    def check_stream_endpoint(self, endpoint, mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        post = self.test_client.post('/api/auth', content_type="application/json",
                             data=json.dumps(dict(username='admin', password='admin')), follow_redirects=True)
        key = json.loads(post.get_data(as_text=True))['access_token']
        response = self.test_client.get('/api/streams/workflowqueue/{}?access_token={}'.format(endpoint, key))
        mock_stream.assert_called_once_with()
        self.assertEqual(response.status_code, SUCCESS)

    def check_stream_endpoint_no_key(self, endpoint, mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        response = self.test_client.get('/api/streams/workflowqueue/{}?access_token=invalid'.format(endpoint))
        mock_stream.assert_not_called()
        self.assertEqual(response.status_code, 422)

    @patch.object(action_stream, 'stream')
    def test_action_stream_endpoint(self, mock_stream):
        self.check_stream_endpoint('actions', mock_stream)

    @patch.object(workflow_stream, 'stream')
    def test_workflow_stream_endpoint(self, mock_stream):
        self.check_stream_endpoint('workflow_status', mock_stream)

    @patch.object(action_stream, 'stream')
    def test_action_stream_endpoint_invalid_key(self, mock_stream):
        self.check_stream_endpoint_no_key('actions', mock_stream)

    @patch.object(workflow_stream, 'stream')
    def test_workflow_stream_endpoint_invalid_key(self, mock_stream):
        self.check_stream_endpoint_no_key('workflow_status', mock_stream)
