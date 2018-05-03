import json
import logging
import os

import gevent
import nacl.bindings
import nacl.utils
import zmq.auth as auth
import zmq.green as zmq
from google.protobuf.json_format import MessageToDict
from nacl.public import PrivateKey, Box
from six import string_types

import walkoff.config
from walkoff.events import WalkoffEvent, EventType
from walkoff.helpers import json_dumps_or_string
from walkoff.proto.build.data_pb2 import Message, CommunicationPacket, ExecuteWorkflowMessage, CaseControl, \
    WorkflowControl

logger = logging.getLogger(__name__)


class WorkflowExecutionController:
    def __init__(self, cache):
        """Initialize a LoadBalancer object, which manages workflow execution.

        Args:
            cache (Cache): The Cache object
        """
        server_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "client.key_secret")
        _, client_secret = auth.load_certificate(client_secret_file)

        self.comm_socket = zmq.Context.instance().socket(zmq.PUB)
        self.comm_socket.curve_secretkey = server_secret
        self.comm_socket.curve_publickey = server_public
        self.comm_socket.curve_server = True
        self.comm_socket.bind(walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS)
        self.cache = cache
        key = PrivateKey(server_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES])
        worker_key = PrivateKey(client_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES]).public_key
        self.box = Box(key, worker_key)

    def add_workflow(self, workflow_id, workflow_execution_id, start=None, start_arguments=None, resume=False):
        """Adds a workflow ID to the queue to be executed.

        Args:
            workflow_id (UUID): The ID of the workflow to be executed.
            workflow_execution_id (UUID): The execution ID of the workflow to be executed.
            start (UUID, optional): The ID of the first, or starting action. Defaults to None.
            start_arguments (list[Argument], optional): The arguments to the starting action of the workflow. Defaults
                to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.
        """
        message = ExecuteWorkflowMessage()
        message.workflow_id = str(workflow_id)
        message.workflow_execution_id = workflow_execution_id
        message.resume = resume

        if start:
            message.start = str(start)
        if start_arguments:
            self._set_arguments_for_proto(message, start_arguments)

        message = message.SerializeToString()
        encrypted_message = self.box.encrypt(message)
        self.cache.lpush("request_queue", encrypted_message)

    def pause_workflow(self, workflow_execution_id):
        """Pauses a workflow currently executing.

        Args:
            workflow_execution_id (UUID): The execution ID of the workflow.
        """
        logger.info('Pausing workflow {0}'.format(workflow_execution_id))
        message = self._create_workflow_control_message(WorkflowControl.PAUSE, workflow_execution_id)
        self._send_message(message)

    def abort_workflow(self, workflow_execution_id):
        """Aborts a workflow currently executing.

        Args:
            workflow_execution_id (UUID): The execution ID of the workflow.
        """
        logger.info('Aborting running workflow {0}'.format(workflow_execution_id))
        message = self._create_workflow_control_message(WorkflowControl.ABORT, workflow_execution_id)
        self._send_message(message)

    @staticmethod
    def _create_workflow_control_message(control_type, workflow_execution_id):
        message = CommunicationPacket()
        message.type = CommunicationPacket.WORKFLOW
        message.workflow_control_message.type = control_type
        message.workflow_control_message.workflow_execution_id = workflow_execution_id
        return message

    def send_exit_to_worker_comms(self):
        """Sends the exit message over the communication sockets, otherwise worker receiver threads will hang"""
        message = CommunicationPacket()
        message.type = CommunicationPacket.EXIT
        self._send_message(message)

    @staticmethod
    def _set_arguments_for_proto(message, arguments):
        for argument in arguments:
            arg = message.arguments.add()
            arg.name = argument.name
            for field in ('value', 'reference', 'selection'):
                val = getattr(argument, field)
                if val is not None:
                    if not isinstance(val, string_types):
                        setattr(arg, field, json_dumps_or_string(val))
                    else:
                        setattr(arg, field, val)

    def create_case(self, case_id, subscriptions):
        """Creates a Case

        Args:
            case_id (int): The ID of the Case
            subscriptions (list[Subscription]): List of Subscriptions to subscribe to
        """
        message = self._create_case_update_message(case_id, CaseControl.CREATE, subscriptions=subscriptions)
        self._send_message(message)

    def update_case(self, case_id, subscriptions):
        """Updates a Case

        Args:
            case_id (int): The ID of the Case
            subscriptions (list[Subscription]): List of Subscriptions to subscribe to
        """
        message = self._create_case_update_message(case_id, CaseControl.UPDATE, subscriptions=subscriptions)
        self._send_message(message)

    def delete_case(self, case_id):
        """Deletes a Case

        Args:
            case_id (int): The ID of the Case to delete
        """
        message = self._create_case_update_message(case_id, CaseControl.DELETE)
        self._send_message(message)

    @staticmethod
    def _create_case_update_message(case_id, message_type, subscriptions=None):
        message = CommunicationPacket()
        message.type = CommunicationPacket.CASE
        message.case_control_message.id = case_id
        message.case_control_message.type = message_type
        subscriptions = subscriptions or []
        for subscription in subscriptions:
            sub = message.case_control_message.subscriptions.add()
            sub.id = subscription.id
            sub.events.extend(subscription.events)
        return message

    def _send_message(self, message):
        message_bytes = message.SerializeToString()
        self.comm_socket.send(message_bytes)


class Receiver:
    def __init__(self, current_app):
        """Initialize a Receiver object, which will receive callbacks from the ExecutionElements.

        Args:
            current_app (Flask.App): The current Flask app
        """
        ctx = zmq.Context.instance()
        self.thread_exit = False
        self.workflows_executed = 0

        server_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)

        self.results_sock = ctx.socket(zmq.PULL)
        self.results_sock.curve_secretkey = server_secret
        self.results_sock.curve_publickey = server_public
        self.results_sock.curve_server = True
        self.results_sock.bind(walkoff.config.Config.ZMQ_RESULTS_ADDRESS)

        self.current_app = current_app

    def receive_results(self):
        """Keep receiving results from execution elements over a ZMQ socket, and trigger the callbacks"""
        while True:
            if self.thread_exit:
                break
            try:
                message_bytes = self.results_sock.recv(zmq.NOBLOCK)
            except zmq.ZMQError:
                gevent.sleep(0.1)
                continue

            with self.current_app.app_context():
                self._send_callback(message_bytes)

        self.results_sock.close()

    def _send_callback(self, message_bytes):

        message_outer = Message()
        message_outer.ParseFromString(message_bytes)
        callback_name = message_outer.event_name

        if message_outer.type == Message.WORKFLOWPACKET:
            message = message_outer.workflow_packet
        elif message_outer.type == Message.ACTIONPACKET:
            message = message_outer.action_packet
        elif message_outer.type == Message.USERMESSAGE:
            message = message_outer.message_packet
        elif message_outer.type == Message.LOGMESSAGE:
            message = message_outer.logging_packet
        else:
            message = message_outer.general_packet

        if hasattr(message, "sender"):
            sender = MessageToDict(message.sender, preserving_proto_field_name=True)
        elif hasattr(message, "workflow"):
            sender = MessageToDict(message.workflow, preserving_proto_field_name=True)
        event = WalkoffEvent.get_event_from_name(callback_name)
        if event is not None:
            data = self._format_data(event, message)
            with self.current_app.app_context():
                event.send(sender, data=data)
            if event in [WalkoffEvent.WorkflowShutdown, WalkoffEvent.WorkflowAborted]:
                self._increment_execution_count()
        else:
            logger.error('Unknown callback {} sent'.format(callback_name))

    @staticmethod
    def _format_data(event, message):
        if event == WalkoffEvent.ConsoleLog:
            data = MessageToDict(message, preserving_proto_field_name=True)
        elif event.event_type != EventType.workflow:
            data = {'workflow': MessageToDict(message.workflow, preserving_proto_field_name=True)}
        else:
            data = {}
        if event.requires_data():
            if event != WalkoffEvent.SendMessage:
                data['data'] = json.loads(message.additional_data)
            else:
                data['message'] = format_message_event_data(message)
        return data

    def _increment_execution_count(self):
        self.workflows_executed += 1


def format_message_event_data(message):
    """Formats a Message

    Args:
        message (Message): The Message to be formatted

    Returns:
        (dict): The formatted Message object
    """
    return {'users': message.users,
            'roles': message.roles,
            'requires_reauth': message.requires_reauth,
            'body': json.loads(message.body),
            'subject': message.subject}
