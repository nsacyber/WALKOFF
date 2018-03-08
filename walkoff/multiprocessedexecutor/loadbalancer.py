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

import walkoff.cache
import walkoff.config.config
import walkoff.config.paths
from walkoff.events import WalkoffEvent, EventType
from walkoff.proto.build.data_pb2 import Message, CommunicationPacket, ExecuteWorkflowMessage

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

logger = logging.getLogger(__name__)


class LoadBalancer:
    def __init__(self, ctx):
        """Initialize a LoadBalancer object, which manages workflow execution.

        Args:
            ctx (Context object): A Context object, shared with the Receiver thread.
        """

        self.thread_exit = False

        self.ctx = ctx
        server_secret_file = os.path.join(walkoff.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(walkoff.config.paths.zmq_private_keys_path, "client.key_secret")
        _, client_secret = auth.load_certificate(client_secret_file)

        self.comm_socket = self.ctx.socket(zmq.PUB)
        self.comm_socket.curve_secretkey = server_secret
        self.comm_socket.curve_publickey = server_public
        self.comm_socket.curve_server = True
        self.comm_socket.bind(walkoff.config.config.zmq_communication_address)

        self.key = PrivateKey(server_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES])
        self.worker_key = PrivateKey(client_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES]).public_key

    def add_workflow(self, workflow_id, workflow_execution_id, start=None, start_arguments=None, resume=False):
        """Adds a workflow ID to the queue to be executed.

        Args:
            workflow_id (int): The ID of the workflow to be executed.
            workflow_execution_id (str): The execution ID of the workflow to be executed.
            start (str, optional): The ID of the first, or starting action. Defaults to None.
            start_arguments (list[Argument]): The arguments to the starting action of the workflow. Defaults to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.
        """
        message = ExecuteWorkflowMessage()
        message.workflow_id = str(workflow_id)
        message.workflow_execution_id = workflow_execution_id
        message.resume = resume

        if start:
            message.start = str(start)
        if start_arguments:
            self.__set_arguments_for_proto(message, start_arguments)

        message = message.SerializeToString()
        box = Box(self.key, self.worker_key)
        enc_message = box.encrypt(message)

        walkoff.cache.cache.lpush("request_queue", enc_message)

    def pause_workflow(self, workflow_execution_id):
        """Pauses a workflow currently executing.

        Args:
            workflow_execution_id (str): The execution ID of the workflow.
        """
        logger.info('Pausing workflow {0}'.format(workflow_execution_id))
        message = CommunicationPacket()
        message.type = CommunicationPacket.PAUSE
        message.workflow_execution_id = workflow_execution_id
        message_bytes = message.SerializeToString()
        self.comm_socket.send(message_bytes)

    def abort_workflow(self, workflow_execution_id):
        """Aborts a workflow currently executing.

        Args:
            workflow_execution_id (str): The execution ID of the workflow.
        """
        logger.info('Aborting workflow {0}'.format(workflow_execution_id))
        message = CommunicationPacket()
        message.type = CommunicationPacket.ABORT
        message.workflow_execution_id = workflow_execution_id
        message_bytes = message.SerializeToString()
        self.comm_socket.send(message_bytes)

    def send_exit_to_worker_comms(self):
        """Sends the exit message over the communication sockets, otherwise worker receiver threads will hang
        """
        message = CommunicationPacket()
        message.type = CommunicationPacket.EXIT
        message_bytes = message.SerializeToString()
        self.comm_socket.send(message_bytes)

    @staticmethod
    def __set_arguments_for_proto(message, arguments):
        for argument in arguments:
            arg = message.arguments.add()
            arg.name = argument.name
            for field in ('value', 'reference', 'selection'):
                val = getattr(argument, field)
                if val is not None:
                    if not isinstance(val, string_types):
                        try:
                            setattr(arg, field, json.dumps(val))
                        except ValueError:
                            setattr(arg, field, str(val))
                    else:
                        setattr(arg, field, val)


class Receiver:
    def __init__(self, ctx):
        """Initialize a Receiver object, which will receive callbacks from the execution elements.

        Args:
            ctx (Context object): A Context object, shared with the LoadBalancer thread.
        """
        self.thread_exit = False
        self.workflows_executed = 0

        server_secret_file = os.path.join(walkoff.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)

        self.ctx = ctx

        self.results_sock = self.ctx.socket(zmq.PULL)
        self.results_sock.curve_secretkey = server_secret
        self.results_sock.curve_publickey = server_public
        self.results_sock.curve_server = True
        self.results_sock.bind(walkoff.config.config.zmq_results_address)

    def receive_results(self):
        """Keep receiving results from execution elements over a ZMQ socket, and trigger the callbacks.
        """

        while True:
            if self.thread_exit:
                break
            try:
                message_bytes = self.results_sock.recv(zmq.NOBLOCK)
            except zmq.ZMQError:
                gevent.sleep(0.1)
                continue

            self.send_callback(message_bytes)

        self.results_sock.close()
        return

    def send_callback(self, message_bytes):
        message_outer = Message()
        message_outer.ParseFromString(message_bytes)
        callback_name = message_outer.event_name
        if message_outer.type == Message.WORKFLOWPACKET:
            message = message_outer.workflow_packet
        elif message_outer.type == Message.ACTIONPACKET:
            message = message_outer.action_packet
        elif message_outer.type == Message.USERMESSAGE:
            message = message_outer.message_packet
        else:
            message = message_outer.general_packet
        sender = MessageToDict(message.sender, preserving_proto_field_name=True)
        event = WalkoffEvent.get_event_from_name(callback_name)
        if event is not None:
            if event.event_type != EventType.workflow:
                data = {'workflow': MessageToDict(message.workflow, preserving_proto_field_name=True)}
            else:
                data = {}
            if event.requires_data():
                if event != WalkoffEvent.SendMessage:
                    data['data'] = json.loads(message.additional_data)
                else:
                    data['message'] = format_message_event_data(message)
            event.send(sender, data=data)
            if event in [WalkoffEvent.WorkflowShutdown, WalkoffEvent.WorkflowAborted]:
                self._increment_execution_count()
        else:
            logger.error('Unknown callback {} sent'.format(callback_name))

    def _increment_execution_count(self):
        self.workflows_executed += 1


def format_message_event_data(message):
    return {'users': message.users,
            'roles': message.roles,
            'requires_reauth': message.requires_reauth,
            'body': json.loads(message.body),
            'subject': message.subject}
