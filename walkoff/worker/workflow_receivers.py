from collections import namedtuple

import zmq
from enum import Enum
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import DecodeError
from nacl.exceptions import CryptoError
from nacl.public import Box
from zmq import ZMQError

import walkoff.cache
import walkoff.config
from walkoff.case.subscription import Subscription
from walkoff.events import WalkoffEvent
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.environment_variable import EnvironmentVariable
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.multiprocessedexecutor.proto_helpers import convert_to_protobuf
from walkoff.proto.build.data_pb2 import CommunicationPacket, WorkflowControl, CaseControl, ExecuteWorkflowMessage
from walkoff.worker.worker import logger


class WorkflowResultsHandler(object):
    def __init__(self, socket_id, execution_db, case_logger):
        """Initialize a WorkflowResultsHandler object, which will be sending results of workflow execution

        Args:
            socket_id (str): The ID for the results socket
            execution_db (ExecutionDatabase): An ExecutionDatabase connection object
            case_logger (CaseLoger): A CaseLogger instance
        """
        self.results_sock = zmq.Context().socket(zmq.PUSH)
        self.results_sock.identity = socket_id
        self.results_sock.curve_secretkey = walkoff.config.Config.CLIENT_PRIVATE_KEY
        self.results_sock.curve_publickey = walkoff.config.Config.CLIENT_PUBLIC_KEY
        self.results_sock.curve_serverkey = walkoff.config.Config.SERVER_PUBLIC_KEY
        try:
            self.results_sock.connect(walkoff.config.Config.ZMQ_RESULTS_ADDRESS)
        except ZMQError:
            logger.exception('Workflow Results handler could not connect to {}!'.format(walkoff.config.Config.ZMQ_RESULTS_ADDRESS))
            raise

        self.execution_db = execution_db

        self.case_logger = case_logger

    def shutdown(self):
        """Shuts down the results socket and tears down the ExecutionDatabase
        """
        self.results_sock.close()
        self.execution_db.tear_down()

    def handle_event(self, workflow_ctx, sender, **kwargs):
        """Listens for the data_sent callback, which signifies that an execution element needs to trigger a
                callback in the main thread.

            Args:
                workflow_ctx (WorkflowExecutionContext): The WorkflowExecutionContext object that triggered the event
                sender (ExecutionElement): The execution element that sent the signal.
                kwargs (dict): Any extra data to send.
        """
        event = kwargs['event']
        if event in [WalkoffEvent.TriggerActionAwaitingData, WalkoffEvent.WorkflowPaused]:
            saved_workflow = SavedWorkflow.from_workflow(workflow_ctx)
            self.execution_db.session.add(saved_workflow)
            self.execution_db.session.commit()
        elif kwargs['event'] == WalkoffEvent.ConsoleLog:
            action = workflow_ctx.get_executing_action()
            sender = action

        packet_bytes = convert_to_protobuf(sender, workflow_ctx, **kwargs)
        if event.is_loggable():
            self.case_logger.log(event, sender.id, kwargs.get('data', None))
        self.results_sock.send(packet_bytes)


class WorkerCommunicationMessageType(Enum):
    workflow = 1
    case = 2
    exit = 3


class WorkflowCommunicationMessageType(Enum):
    pause = 1
    abort = 2


class CaseCommunicationMessageType(Enum):
    create = 1
    update = 2
    delete = 3


WorkerCommunicationMessageData = namedtuple('WorkerCommunicationMessageData', ['type', 'data'])
WorkflowCommunicationMessageData = namedtuple('WorkflowCommunicationMessageData', ['type', 'workflow_execution_id'])
CaseCommunicationMessageData = namedtuple('CaseCommunicationMessageData', ['type', 'case_id', 'subscriptions'])


class WorkflowCommunicationReceiver(object):
    def __init__(self, socket_id):
        """Initialize a WorkflowCommunicationReceiver object, which will receive messages on the comm socket

        Args:
            socket_id (str): The socket ID for the ZMQ communication socket
        """
        self.comm_sock = zmq.Context().socket(zmq.SUB)
        self.comm_sock.identity = socket_id
        self.comm_sock.curve_secretkey = walkoff.config.Config.CLIENT_PRIVATE_KEY
        self.comm_sock.curve_publickey = walkoff.config.Config.CLIENT_PUBLIC_KEY
        self.comm_sock.curve_serverkey = walkoff.config.Config.SERVER_PUBLIC_KEY
        self.comm_sock.setsockopt(zmq.SUBSCRIBE, b'')
        try:
            self.comm_sock.connect(walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS)
        except ZMQError:
            logger.exception('Workflow Communication Receiver could not connect to {}!'.format(
                walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS))
            raise
        self.exit = False

    def shutdown(self):
        """Shuts down the object by setting self.exit to True and closing the communication socket
        """
        logger.debug('Shutting down Workflow Communication Recevier')
        self.exit = True
        self.comm_sock.close()

    def receive_communications(self):
        """Constantly receives data from the ZMQ socket and handles it accordingly"""
        logger.info('Starting workflow communication receiver')
        while not self.exit:
            try:
                message_bytes = self.comm_sock.recv()
            except zmq.ZMQError:
                continue

            message = CommunicationPacket()
            try:
                message.ParseFromString(message_bytes)
            except DecodeError:
                logger.error('Worker communication handler could not decode communication packet')
            else:
                message_type = message.type
                if message_type == CommunicationPacket.WORKFLOW:
                    logger.debug('Worker received workflow communication packet')
                    yield WorkerCommunicationMessageData(
                        WorkerCommunicationMessageType.workflow,
                        self._format_workflow_message_data(message.workflow_control_message))
                elif message_type == CommunicationPacket.CASE:
                    logger.debug('Workflow received case communication packet')
                    yield WorkerCommunicationMessageData(
                        WorkerCommunicationMessageType.case,
                        self._format_case_message_data(message.case_control_message))
                elif message_type == CommunicationPacket.EXIT:
                    logger.info('Worker received exit message')
                    break
        raise StopIteration

    @staticmethod
    def _format_workflow_message_data(message):
        workflow_execution_id = message.workflow_execution_id
        if message.type == WorkflowControl.PAUSE:
            return WorkflowCommunicationMessageData(WorkflowCommunicationMessageType.pause, workflow_execution_id)
        elif message.type == WorkflowControl.ABORT:
            return WorkflowCommunicationMessageData(WorkflowCommunicationMessageType.abort, workflow_execution_id)

    @staticmethod
    def _format_case_message_data(message):
        if message.type == CaseControl.CREATE:
            return CaseCommunicationMessageData(
                CaseCommunicationMessageType.create,
                message.id,
                [Subscription(sub.id, sub.events) for sub in message.subscriptions])
        elif message.type == CaseControl.UPDATE:
            return CaseCommunicationMessageData(
                CaseCommunicationMessageType.update,
                message.id,
                [Subscription(sub.id, sub.events) for sub in message.subscriptions])
        elif message.type == CaseControl.DELETE:
            return CaseCommunicationMessageData(CaseCommunicationMessageType.delete, message.id, None)


class WorkflowReceiver(object):
    def __init__(self, key, server_key, cache_config):
        """Initializes a WorkflowReceiver object, which receives workflow execution requests and ships them off to a
            worker to execute

        Args:
            key (PrivateKey): The NaCl PrivateKey generated by the Worker
            server_key (PrivateKey): The NaCl PrivateKey generated by the Worker
            cache_config (dict): Cache configuration
        """
        self.key = key
        self.server_key = server_key
        self.cache = walkoff.cache.make_cache(cache_config)
        self.exit = False

    def shutdown(self):
        """Shuts down the object by setting self.exit to True and shutting down the cache
        """
        logger.debug('Shutting down Workflow Receiver')
        self.exit = True
        self.cache.shutdown()

    def receive_workflows(self):
        """Receives requests to execute workflows, and sends them off to worker threads"""
        logger.info('Starting workflow receiver')
        box = Box(self.key, self.server_key)
        while not self.exit:
            received_message = self.cache.rpop("request_queue")
            if received_message is not None:
                try:
                    decrypted_msg = box.decrypt(received_message)
                except CryptoError:
                    logger.error('Worker could not decrypt received workflow message')
                    continue
                try:
                    message = ExecuteWorkflowMessage()
                    message.ParseFromString(decrypted_msg)
                except DecodeError:
                    logger.error('Workflow could not decode received workflow message')
                else:
                    start = message.start if hasattr(message, 'start') else None

                    start_arguments = []
                    if hasattr(message, 'arguments'):
                        for arg in message.arguments:
                            start_arguments.append(
                                Argument(**(MessageToDict(arg, preserving_proto_field_name=True))))

                    env_vars = []
                    if hasattr(message, 'environment_variables'):
                        for env_var in message.environment_variables:
                            env_vars.append(
                                EnvironmentVariable(**(MessageToDict(env_var, preserving_proto_field_name=True))))

                    yield message.workflow_id, message.workflow_execution_id, start, \
                          start_arguments, message.resume, env_vars
            else:
                yield None
        raise StopIteration