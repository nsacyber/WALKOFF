from unittest import TestCase
from uuid import uuid4

from mock import patch
from zmq import Socket, auth

from walkoff.config import Config
from walkoff.multiprocessedexecutor.worker import *


class TestWorkflowResultsHandler(TestCase):

    @classmethod
    def setUpClass(cls):
        Config.load_env_vars()
        server_secret_file = os.path.join(Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        cls.server_public, cls.server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(Config.ZMQ_PRIVATE_KEYS_PATH, "client.key_secret")
        cls.client_public, cls.client_secret = auth.load_certificate(client_secret_file)

    def test_init(self):
        with patch.object(Socket, 'connect') as mock_connect:
            socket_id = b'test_id'
            address = 'tcp://127.0.0.1:5557'
            receiver = WorkflowCommunicationReceiver(socket_id)
            mock_connect.assert_called_once_with(address)
            self.assertFalse(receiver.exit)

    def get_receiver(self):
        with patch.object(Socket, 'connect'):
            socket_id = b'test_id'
            receiver = WorkflowCommunicationReceiver(socket_id)
            return receiver

    def test_shutdown(self):
        receiver = self.get_receiver()
        with patch.object(receiver.comm_sock, 'close') as mock_close:
            receiver.shutdown()
            mock_close.assert_called_once()
            self.assertTrue(receiver.exit)

    def check_receive_communication_message(self, receiver, message, expected_response):
        with patch.object(receiver.comm_sock, 'recv', return_value=message.SerializeToString()):
            message_generator = receiver.receive_communications()
            message = next(message_generator)
            self.assertEqual(message, expected_response)

    def check_receive_workflow_communication_message(self, proto_message_type, data_message_type):
        receiver = self.get_receiver()
        message = CommunicationPacket()
        message.type = CommunicationPacket.WORKFLOW
        message.workflow_control_message.type = proto_message_type
        uid = str(uuid4())
        message.workflow_control_message.workflow_execution_id = uid
        expected = WorkerCommunicationMessageData(
            WorkerCommunicationMessageType.workflow,
            WorkflowCommunicationMessageData(data_message_type, uid))
        self.check_receive_communication_message(receiver, message, expected)

    def test_receive_workflow_pause(self):
        self.check_receive_workflow_communication_message(WorkflowControl.PAUSE, WorkflowCommunicationMessageType.pause)

    def test_receive_workflow_abort(self):
        self.check_receive_workflow_communication_message(WorkflowControl.ABORT, WorkflowCommunicationMessageType.abort)

    def check_receive_case_communication_message(self, proto_message_type, data_message_type, is_delete=False):
        receiver = self.get_receiver()
        message = CommunicationPacket()
        message.type = CommunicationPacket.CASE
        message.case_control_message.type = proto_message_type
        case_id = 42
        message.case_control_message.id = case_id
        ids = [str(uuid4()), str(uuid4())]
        event_sets = [['a', 'b'], ['c', 'd']]
        for id_, events in zip(ids, event_sets):
            sub = message.case_control_message.subscriptions.add()
            sub.id = id_
            sub.events.extend(events)
        subscriptions = [Subscription(id_, events) for id_, events in zip(ids, event_sets)]
        expected = WorkerCommunicationMessageData(
            WorkerCommunicationMessageType.case,
            CaseCommunicationMessageData(data_message_type, case_id, subscriptions))
        self.check_receive_communication_message(receiver, message, expected)

    def test_receive_create_case(self):
        self.check_receive_case_communication_message(CaseControl.CREATE, CaseCommunicationMessageType.create)

    def test_receive_update_case(self):
        self.check_receive_case_communication_message(CaseControl.UPDATE, CaseCommunicationMessageType.update)

    def test_receive_delete_case(self):
        receiver = self.get_receiver()
        message = CommunicationPacket()
        message.type = CommunicationPacket.CASE
        message.case_control_message.type = CaseControl.DELETE
        case_id = 42
        message.case_control_message.id = case_id
        expected = WorkerCommunicationMessageData(
            WorkerCommunicationMessageType.case,
            CaseCommunicationMessageData(CaseCommunicationMessageType.delete, case_id, None))
        self.check_receive_communication_message(receiver, message, expected)

    def test_receive_exit(self):
        receiver = self.get_receiver()
        message = CommunicationPacket()
        message.type = CommunicationPacket.EXIT
        with patch.object(receiver.comm_sock, 'recv', return_value=message.SerializeToString()):
            message_generator = receiver.receive_communications()
            with self.assertRaises(StopIteration):
                message = next(message_generator)
