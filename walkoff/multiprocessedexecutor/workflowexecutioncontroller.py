import logging
import os

import nacl.bindings
import nacl.utils
import zmq.auth as auth
import zmq.green as zmq
from nacl.public import PrivateKey, Box
from six import string_types

import walkoff.config
from walkoff.helpers import json_dumps_or_string
from walkoff.proto.build.data_pb2 import CommunicationPacket, ExecuteWorkflowMessage, CaseControl, \
    WorkflowControl
from walkoff.multiprocessedexecutor import proto_helpers

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

        self.comm_sock = zmq.Context.instance().socket(zmq.PUB)
        self.comm_sock.curve_secretkey = server_secret
        self.comm_sock.curve_publickey = server_public
        self.comm_sock.curve_server = True
        self.comm_sock.bind(walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS)
        self.cache = cache
        key = PrivateKey(server_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES])
        worker_key = PrivateKey(client_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES]).public_key
        self.box = Box(key, worker_key)

    def add_workflow(self, workflow_id, workflow_execution_id, start=None, start_arguments=None, resume=False,
                     environment_variables=None):
        """Adds a workflow ID to the queue to be executed.

        Args:
            workflow_id (UUID): The ID of the workflow to be executed.
            workflow_execution_id (UUID): The execution ID of the workflow to be executed.
            start (UUID, optional): The ID of the first, or starting action. Defaults to None.
            start_arguments (list[Argument], optional): The arguments to the starting action of the workflow. Defaults
                to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.
            environment_variables (list[EnvironmentVariable]): Optional list of environment variables to pass into
                the workflow. These will not be persistent.
        """
        message = ExecuteWorkflowMessage()
        message.workflow_id = str(workflow_id)
        message.workflow_execution_id = workflow_execution_id
        message.resume = resume

        if start:
            message.start = str(start)
        if start_arguments:
            self._set_arguments_for_proto(message, start_arguments)
        if environment_variables:
            proto_helpers.add_env_vars_to_proto(message, environment_variables)

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
        self.comm_sock.send(message_bytes)
