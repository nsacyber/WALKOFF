from unittest import TestCase
from zmq import Socket
from mock import patch, create_autospec
from walkoff.multiprocessedexecutor.workflowexecutioncontroller import WorkflowExecutionController, Message, CaseControl, CommunicationPacket, WorkflowControl
from walkoff.case.subscription import Subscription
from uuid import uuid4


class TestWorkflowExecutionController(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.subscriptions = [Subscription(str(uuid4()), ['a', 'b', 'c']), Subscription(str(uuid4()), ['b'])]
        cls.controller = WorkflowExecutionController()

    @classmethod
    def tearDown(cls):
        cls.controller.comm_socket.close()

    @staticmethod
    def assert_message_sent(mock_send, expected_message):
        mock_send.assert_called_once()
        mock_send.assert_called_with(expected_message, 1, True, False)

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
    def test_add_case(self, mock_send):
        self.controller.add_case(14, self.subscriptions)
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

    