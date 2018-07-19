from unittest import TestCase
from uuid import uuid4

import os.path
from mock import patch, create_autospec
from sqlalchemy.orm import scoped_session
from zmq import Socket
from zmq import auth

import walkoff.multiprocessedexecutor.worker
from walkoff.case.logger import CaseLogger
from walkoff.config import Config
from walkoff.events import WalkoffEvent
from walkoff.executiondb import ExecutionDatabase
from walkoff.executiondb.workflow import Workflow
from walkoff.multiprocessedexecutor.worker import WorkflowResultsHandler


class MockSender(object):
    def __init__(self, id_):
        self.id = id_


class TestWorkflowResultsHandler(TestCase):

    @classmethod
    def setUpClass(cls):
        server_secret_file = os.path.join(Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        cls.server_public, cls.server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(Config.ZMQ_PRIVATE_KEYS_PATH, "client.key_secret")
        cls.client_public, cls.client_secret = auth.load_certificate(client_secret_file)

    def test_init(self):
        with patch.object(Socket, 'connect') as mock_connect:
            logger = create_autospec(CaseLogger)
            database = create_autospec(ExecutionDatabase)
            socket_id = b'test_id'
            address = '127.0.0.1:5557'
            handler = WorkflowResultsHandler(
                socket_id,
                self.client_secret,
                self.client_public,
                self.server_public,
                address,
                database,
                logger)
            mock_connect.assert_called_once_with(address)
            self.assertEqual(handler.execution_db, database)
            self.assertEqual(handler.case_logger, logger)

    def get_handler(self):
        with patch.object(Socket, 'connect'):
            logger = create_autospec(CaseLogger)
            database = create_autospec(ExecutionDatabase)
            socket_id = b'test_id'
            address = '127.0.0.1:5557'
            handler = WorkflowResultsHandler(
                socket_id,
                self.client_secret,
                self.client_public,
                self.server_public,
                address,
                database,
                logger)
            return handler, database, logger

    def test_shutdown(self):
        handler, database, _logger = self.get_handler()
        with patch.object(handler.results_sock, 'close') as mock_close:
            handler.shutdown()
            mock_close.assert_called_once()
            database.tear_down.assert_called_once()

    @patch('walkoff.multiprocessedexecutor.worker.convert_to_protobuf', return_value='test_packet')
    def test_handle_event_no_data(self, mock_convert):
        handler, _database, logger = self.get_handler()
        with patch.object(handler.results_sock, 'send') as mock_send:
            uid = uuid4()
            sender = MockSender(uid)
            handler.handle_event('aa', sender, event=WalkoffEvent.WorkflowExecutionStart)
            mock_convert.assert_called_once_with(sender, 'aa', event=WalkoffEvent.WorkflowExecutionStart)
            logger.log.assert_called_once_with(WalkoffEvent.WorkflowExecutionStart, uid, None)
            mock_send.assert_called_once_with('test_packet')

    @patch('walkoff.multiprocessedexecutor.worker.convert_to_protobuf', return_value='test_packet')
    def test_handle_event_with_data(self, mock_convert):
        handler, _database, logger = self.get_handler()
        with patch.object(handler.results_sock, 'send') as mock_send:
            uid = uuid4()
            sender = MockSender(uid)
            data = {'a': 42}
            handler.handle_event('aa', sender, event=WalkoffEvent.WorkflowExecutionStart, data=data)
            mock_convert.assert_called_once_with(sender, 'aa', event=WalkoffEvent.WorkflowExecutionStart, data=data)
            logger.log.assert_called_once_with(WalkoffEvent.WorkflowExecutionStart, uid, data)
            mock_send.assert_called_once_with('test_packet')

    def check_handle_saved_event(self, mock_saved_workflow, mock_convert, event):
        handler, database, logger = self.get_handler()
        with patch.object(handler.results_sock, 'send') as mock_send:
            database.session = create_autospec(scoped_session)
            uid = uuid4()
            sender = MockSender(uid)
            handler.handle_event('aa', sender, event=event)
            mock_saved_workflow.assert_called_once_with('aa')
            database.session.add.assert_called_once_with('saved_workflow')
            database.session.commit.assert_called_once()
            mock_convert.assert_called_once_with(sender, 'aa', event=event)
            logger.log.assert_called_once_with(event, uid, None)
            mock_send.assert_called_once_with('test_packet')

    @patch('walkoff.multiprocessedexecutor.worker.convert_to_protobuf', return_value='test_packet')
    @patch.object(walkoff.multiprocessedexecutor.worker.SavedWorkflow, 'from_workflow', return_value='saved_workflow')
    def test_handle_pause_event(self, mock_saved_workflow, mock_convert):
        self.check_handle_saved_event(mock_saved_workflow, mock_convert, WalkoffEvent.WorkflowPaused)

    @patch('walkoff.multiprocessedexecutor.worker.convert_to_protobuf', return_value='test_packet')
    @patch.object(walkoff.multiprocessedexecutor.worker.SavedWorkflow, 'from_workflow', return_value='saved_workflow')
    def test_handle_trigger_save_event(self, mock_saved_workflow, mock_convert):
        self.check_handle_saved_event(mock_saved_workflow, mock_convert, WalkoffEvent.TriggerActionAwaitingData)

    @patch('walkoff.multiprocessedexecutor.worker.convert_to_protobuf', return_value='test_packet')
    def test_handle_console_log_event(self, mock_convert):
        handler, _database, logger = self.get_handler()
        workflow = create_autospec(Workflow)
        action = MockSender('action')
        workflow.get_executing_action = lambda: action
        with patch.object(handler.results_sock, 'send') as mock_send:
            uid = uuid4()
            sender = MockSender(uid)
            data = {'a': 42}
            handler.handle_event(workflow, sender, event=WalkoffEvent.ConsoleLog, data=data)
            mock_convert.assert_called_once_with(action, workflow, event=WalkoffEvent.ConsoleLog, data=data)
            mock_send.assert_called_once_with('test_packet')
