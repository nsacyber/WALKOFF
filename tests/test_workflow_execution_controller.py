import json
from unittest import TestCase
from uuid import uuid4

from mock import patch
from zmq import Socket

from tests.util import initialize_test_config
from tests.util.execution_db_help import setup_dbs
from tests.util.mock_objects import MockRedisCacheAdapter
from walkoff.case.subscription import Subscription
from walkoff.executiondb.argument import Argument
from walkoff.multiprocessedexecutor.workflowexecutioncontroller import ExecuteWorkflowMessage, \
    WorkflowExecutionController, Message, CaseControl, CommunicationPacket, WorkflowControl
from walkoff.multiprocessedexecutor.proto_helpers import add_arguments_to_proto


class TestWorkflowExecutionController(TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        cls.subscriptions = [Subscription(str(uuid4()), ['a', 'b', 'c']), Subscription(str(uuid4()), ['b'])]
        cls.cache = MockRedisCacheAdapter()
        cls.controller = WorkflowExecutionController(cls.cache)
        setup_dbs()

    def tearDown(self):
        self.cache.clear()

    @classmethod
    def tearDownClass(cls):
        cls.controller.comm_socket.close()

    @staticmethod
    def assert_message_sent(mock_send, expected_message):
        mock_send.assert_called_once()
        mock_send.assert_called_with(expected_message, 1, True, False)  # Not sure why these other args need to exist

    @patch.object(Socket, 'send')
    def test_send_message(self, mock_send):
        self.controller._send_message(Message())
        self.assert_message_sent(mock_send, Message().SerializeToString())

    def test_construct_case_update_message(self):
        message = WorkflowExecutionController._create_case_update_message(
            18,
            CaseControl.CREATE,
            subscriptions=self.subscriptions)
        self.assertEqual(message.type, CommunicationPacket.CASE)
        message = message.case_control_message
        self.assertEqual(message.id, 18)
        self.assertEqual(message.type, CaseControl.CREATE)
        for i in range(2):
            self.assertEqual(message.subscriptions[i].id, self.subscriptions[i].id)
            self.assertEqual(message.subscriptions[i].events, self.subscriptions[i].events)

    def test_construct_case_update_message_no_subscriptions(self):
        message = WorkflowExecutionController._create_case_update_message(18, CaseControl.CREATE)
        self.assertEqual(message.type, CommunicationPacket.CASE)
        message = message.case_control_message
        self.assertEqual(message.id, 18)
        self.assertEqual(message.type, CaseControl.CREATE)
        self.assertEqual(len(message.subscriptions), 0)

    @patch.object(Socket, 'send')
    def test_create_case(self, mock_send):
        self.controller.create_case(14, self.subscriptions)
        expected_message = WorkflowExecutionController._create_case_update_message(
            14,
            CaseControl.CREATE,
            subscriptions=self.subscriptions)
        expected_message = expected_message.SerializeToString()
        self.assert_message_sent(mock_send, expected_message)

    @patch.object(Socket, 'send')
    def test_update_case(self, mock_send):
        self.controller.update_case(14, self.subscriptions)
        expected_message = WorkflowExecutionController._create_case_update_message(
            14,
            CaseControl.UPDATE,
            subscriptions=self.subscriptions)
        expected_message = expected_message.SerializeToString()
        self.assert_message_sent(mock_send, expected_message)

    @patch.object(Socket, 'send')
    def test_delete_case(self, mock_send):
        self.controller.delete_case(37)
        expected_message = WorkflowExecutionController._create_case_update_message(37, CaseControl.DELETE)
        expected_message = expected_message.SerializeToString()
        self.assert_message_sent(mock_send, expected_message)

    @patch.object(Socket, 'send')
    def test_send_exit_to_worker_comms(self, mock_send):
        self.controller.send_exit_to_worker_comms()
        expected_message = CommunicationPacket()
        expected_message.type = CommunicationPacket.EXIT
        expected_message = expected_message.SerializeToString()
        self.assert_message_sent(mock_send, expected_message)

    def test_create_workflow_control_message(self):
        uid = str(uuid4())
        message = WorkflowExecutionController._create_workflow_control_message(WorkflowControl.PAUSE, uid)
        self.assertEqual(message.type, CommunicationPacket.WORKFLOW)
        self.assertEqual(message.workflow_control_message.type, WorkflowControl.PAUSE)
        self.assertEqual(message.workflow_control_message.workflow_execution_id, uid)

    @patch.object(Socket, 'send')
    def test_abort_workflow(self, mock_send):
        uid = str(uuid4())
        message = WorkflowExecutionController._create_workflow_control_message(WorkflowControl.ABORT, uid)
        self.controller.abort_workflow(uid)
        expected_message = message.SerializeToString()
        self.assert_message_sent(mock_send, expected_message)

    @patch.object(Socket, 'send')
    def test_pause_workflow(self, mock_send):
        uid = str(uuid4())
        message = WorkflowExecutionController._create_workflow_control_message(WorkflowControl.PAUSE, uid)
        self.controller.pause_workflow(uid)
        expected_message = message.SerializeToString()
        self.assert_message_sent(mock_send, expected_message)

    def test_set_argumets_for_proto(self):
        message = ExecuteWorkflowMessage()
        uid = uuid4()
        selection = [Argument('test', 1), Argument('test', 'a'), Argument('test', '32'), Argument('test', 46)]
        arguments = [
            Argument('name1', value=32), Argument('name2', reference=uid, selection=selection)]
        add_arguments_to_proto(message.arguments, arguments)
        self.assertEqual(len(message.arguments), len(arguments))
        self.assertEqual(message.arguments[0].name, arguments[0].name)
        self.assertEqual(message.arguments[0].value, str(arguments[0].value))
        self.assertEqual(message.arguments[0].reference, '')
        self.assertEqual(len(message.arguments[0].selection), 0)

        self.assertEqual(message.arguments[1].name, arguments[1].name)
        self.assertEqual(message.arguments[1].value, '')
        self.assertEqual(message.arguments[1].reference, str(uid))
        self.assertEqual(len(message.arguments[1].selection), len(selection))
