import logging
import os
import uuid
from collections import namedtuple
from enum import Enum

import zmq.auth as auth
import zmq.green as zmq
from google.protobuf.message import DecodeError
from zmq import ZMQError

from walkoff.proto.build.data_pb2 import CommunicationPacket, WorkflowControl, CaseControl

logger = logging.getLogger(__name__)


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


class ProtobufWorkflowCommunicationConverter(object):
    @staticmethod
    def _format_workflow_message_data(message):
        workflow_execution_id = message.workflow_execution_id
        if message.type == WorkflowControl.PAUSE:
            return WorkflowCommunicationMessageData(WorkflowCommunicationMessageType.pause, workflow_execution_id)
        elif message.type == WorkflowControl.ABORT:
            return WorkflowCommunicationMessageData(WorkflowCommunicationMessageType.abort, workflow_execution_id)

    @staticmethod
    def to_received_message(message_bytes):
        """Constantly receives data from the ZMQ socket and handles it accordingly"""
        message = CommunicationPacket()
        try:
            message.ParseFromString(message_bytes)
        except DecodeError:
            logger.error('Worker communication handler could not decode communication packet')
        else:
            message_type = message.type
            if message_type == CommunicationPacket.WORKFLOW:
                logger.debug('Worker received workflow communication packet')
                return WorkerCommunicationMessageData(
                    WorkerCommunicationMessageType.workflow,
                    self._format_workflow_message_data(message.workflow_control_message))
            elif message_type == CommunicationPacket.EXIT:
                logger.info('Worker received exit message')
                return None

    @staticmethod
    def _create_workflow_control_message(control_type, workflow_execution_id):
        message = CommunicationPacket()
        message.type = CommunicationPacket.WORKFLOW
        message.workflow_control_message.type = control_type
        message.workflow_control_message.workflow_execution_id = workflow_execution_id
        return message

    @staticmethod
    def create_workflow_pause_message(workflow_execution_id):
        return ProtobufWorkflowCommunicationConverter._create_workflow_control_message(
            WorkflowControl.PAUSE,
            workflow_execution_id
        )

    @staticmethod
    def create_workflow_abort_message(workflow_execution_id):
        return ProtobufWorkflowCommunicationConverter._create_workflow_control_message(
            WorkflowControl.ABORT,
            workflow_execution_id
        )

    @staticmethod
    def create_worker_exit_message():
        message = CommunicationPacket()
        message.type = CommunicationPacket.EXIT
        return message


class ZmqWorkflowCommunicationReceiver(object):
    def __init__(self, socket_id, client_secret_key, client_public_key, server_public_key, zmq_communication_address,
                 message_converter=ProtobufWorkflowCommunicationConverter):
        """Initialize a WorkflowCommunicationReceiver object, which will receive messages on the comm socket

        Args:
            socket_id (str): The socket ID for the ZMQ communication socket
            client_secret_key (str): The secret key for the client
            client_public_key (str): The public key for the client
            server_public_key (str): The public key for the server
            zmq_communication_address (str): The IP address for the ZMQ communication socket
        """
        self.comm_sock = zmq.Context().socket(zmq.SUB)
        self.comm_sock.identity = socket_id
        self.comm_sock.curve_secretkey = client_secret_key
        self.comm_sock.curve_publickey = client_public_key
        self.comm_sock.curve_serverkey = server_public_key
        self.comm_sock.setsockopt(zmq.SUBSCRIBE, b'')
        try:
            self.comm_sock.connect(zmq_communication_address)
        except ZMQError:
            logger.exception('Workflow Communication Receiver could not connect to {}!'.format(
                zmq_communication_address))
            raise
        self.exit = False
        self.message_converter = message_converter

    def shutdown(self):
        """Shuts down the object by setting self.exit to True and closing the communication socket
        """
        logger.debug('Shutting down Workflow Communication Receiver')
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

            message = self.message_converter.to_received_message(message_bytes)
            if message is not None:
                yield message
            else:
                break
        raise StopIteration


class KafkaWorkflowCommunicationReceiver(object):
    _requires = ['confluent-kafka']

    def __init__(
            self,
            config,
            workflow_communication_topic,
            case_communication_topic,
            message_converter=ProtobufWorkflowCommunicationConverter
    ):
        from comfluent_kafka import Consumer
        self.receiver = Consumer(config)
        self.workflow_communication_topic = workflow_communication_topic
        self.case_communication_topic = case_communication_topic
        self.message_converter = message_converter
        self.exit = False

    def shutdown(self):
        self.exit = True
        self.receiver.close()

    def receive_communications(self):
        """Constantly receives data from the ZMQ socket and handles it accordingly"""
        from confluent_kafka import KafkaError
        logger.info('Starting workflow communication receiver')
        while not self.exit:
            raw_message = self.receiver.poll(1.0)
            if raw_message is None:
                continue
            if raw_message.error():
                if raw_message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error('Received an error in Kafka receiver: {}'.format(raw_message.error()))
                    continue

            message = self.message_converter.to_received_message(raw_message.value())
            if message is not None:
                yield message
            else:
                break

        raise StopIteration


class ZmqWorkflowCommunicationSender(object):

    def __init__(self, server_secret, server_public, network_address,
                 message_converter=ProtobufWorkflowCommunicationConverter):
        self.comm_socket = zmq.Context.instance().socket(zmq.PUB)
        self.comm_socket.curve_secretkey = server_secret
        self.comm_socket.curve_publickey = server_public
        self.comm_socket.curve_server = True
        self.comm_socket.bind(network_address)

        self.message_converter = message_converter

    def shutdown(self):
        self.comm_socket.close()

    def pause_workflow(self, workflow_execution_id):
        """Pauses a workflow currently executing.

        Args:
            workflow_execution_id (UUID): The execution ID of the workflow.
        """
        logger.info('Pausing workflow {0}'.format(workflow_execution_id))
        self._send_message(self.message_converter.create_workflow_pause_message(workflow_execution_id))

    def abort_workflow(self, workflow_execution_id):
        """Aborts a workflow currently executing.

        Args:
            workflow_execution_id (UUID): The execution ID of the workflow.
        """
        logger.info('Aborting running workflow {0}'.format(workflow_execution_id))
        self._send_message(self.message_converter.create_workflow_abort_message(workflow_execution_id))

    def send_exit_to_workers(self):
        """Sends the exit message over the communication sockets, otherwise worker receiver threads will hang"""
        self._send_message(self.message_converter.create_worker_exit_message())

    def create_case(self, case_id, subscriptions):
        """Creates a Case

        Args:
            case_id (int): The ID of the Case
            subscriptions (list[Subscription]): List of Subscriptions to subscribe to
        """
        message = self.message_converter.create_case_create_message(case_id, subscriptions)
        self._send_message(message)

    def update_case(self, case_id, subscriptions):
        """Updates a Case

        Args:
            case_id (int): The ID of the Case
            subscriptions (list[Subscription]): List of Subscriptions to subscribe to
        """
        message = self.message_converter.create_case_update_message(case_id, subscriptions)
        self._send_message(message)

    def delete_case(self, case_id):
        """Deletes a Case

        Args:
            case_id (int): The ID of the Case to delete
        """
        message = self.message_converter.create_case_delete_message(case_id)
        self._send_message(message)

    def _send_message(self, message):
        message_bytes = message.SerializeToString()
        self.comm_socket.send(message_bytes)


class KafkaWorkflowCommunicationSender():
    _requires = ['confluent-kafka']

    def __init__(self, config, workflow_communication_topic, case_communication_topic,
                 message_converter=ProtobufWorkflowCommunicationConverter):
        from comfluent_kafka import Producer
        self.producer = Producer(config)
        self.workflow_communication_topic = workflow_communication_topic
        self.case_communication_topic = case_communication_topic
        self.message_converter = message_converter

    def shutdown(self):
        self.producer.flush()

    @staticmethod
    def _delivery_callback(err, msg):
        if err is not None:
            logger.error('Kafka message delivery failed: {}'.format(err))

    def pause_workflow(self, workflow_execution_id):
        """Pauses a workflow currently executing.

        Args:
            workflow_execution_id (UUID): The execution ID of the workflow.
        """
        logger.info('Pausing workflow {0}'.format(workflow_execution_id))
        message = self.message_converter.create_workflow_pause_message(workflow_execution_id)
        self._send_workflow_communication_message(message, workflow_execution_id)

    def abort_workflow(self, workflow_execution_id):
        """Aborts a workflow currently executing.

        Args:
            workflow_execution_id (UUID): The execution ID of the workflow.
        """
        logger.info('Aborting running workflow {0}'.format(workflow_execution_id))
        message = self.message_converter.create_workflow_abort_message(workflow_execution_id)
        self._send_workflow_communication_message(message, workflow_execution_id)

    def send_exit_to_workers(self):
        """Sends the exit message over the communication sockets, otherwise worker receiver threads will hang"""
        message = self.message_converter.create_worker_exit_message()
        self._send_workflow_communication_message(message, None)

    def _send_workflow_communication_message(self, message, workflow_id):
        self._send_message(message, self.workflow_communication_topic, workflow_id)

    def create_case(self, case_id, subscriptions):
        """Creates a Case

        Args:
            case_id (int): The ID of the Case
            subscriptions (list[Subscription]): List of Subscriptions to subscribe to
        """
        message = self.message_converter.create_case_create_message(case_id, subscriptions)
        self._send_case_communication_message(message, case_id)

    def update_case(self, case_id, subscriptions):
        """Updates a Case

        Args:
            case_id (int): The ID of the Case
            subscriptions (list[Subscription]): List of Subscriptions to subscribe to
        """
        message = self.message_converter.create_case_update_message(case_id, subscriptions)
        self._send_case_communication_message(message, case_id)

    def delete_case(self, case_id):
        """Deletes a Case

        Args:
            case_id (int): The ID of the Case to delete
        """
        message = self.message_converter.create_case_delete_message(case_id)
        self._send_case_communication_message(message, case_id)

    def _send_case_communication_message(self, message, case_id):
        self._send_message(message, self.case_communication_topic, case_id)

    def _send_message(self, message, topic, key):
        self.producer.produce(
            topic,
            message,
            key=key,
            callback=self._delivery_callback
        )


def make_zmq_communication_sender(config, protocol_translation, **kwargs):
    try:
        protocol = protocol_translation[config.WORKFLOW_COMMUNICATION_PROTOCOL]
    except KeyError:
        message = 'Could not find communication protocol {}'.format(config.WORKFLOW_COMMUNICATION_PROTOCOL)
        logger.error(message)
        raise ValueError(message)
    else:
        server_secret_file = os.path.join(config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)
        address = config.ZMQ_COMMUNICATION_ADDRESS
        return ZmqWorkflowCommunicationSender(server_secret, server_public, address, message_converter=protocol)


def make_zmq_communication_receiver(config, protocol_translation, **kwargs):
    try:
        protocol = protocol_translation[config.WORKFLOW_COMMUNICATION_PROTOCOL]
    except KeyError:
        message = 'Could not find communication protocol {}'.format(config.WORKFLOW_COMMUNICATION_PROTOCOL)
        logger.error(message)
        raise ValueError(message)
    else:
        server_secret_file = os.path.join(config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public, _server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(config.ZMQ_PRIVATE_KEYS_PATH, "client.key_secret")
        client_public, client_secret = auth.load_certificate(client_secret_file)
        address = config.ZMQ_COMMUNICATION_ADDRESS
        return ZmqWorkflowCommunicationReceiver(
            'Workflow_Communication_Receiver_{}'.format(kwargs.get('id', uuid.uuid4())),
            client_secret,
            client_public,
            server_public,
            address,
            message_converter=protocol
        )


def make_kafka_communication_sender(config, protocol_translation, **kwargs):
    sender = KafkaWorkflowCommunicationSender(
        config.WORKFLOW_COMMUNICATION_KAFKA_CONFIG,
        *_get_kafka_configs(config, protocol_translation)
    )
    return sender


def make_kafka_communication_receiver(config, protocol_translation, **kwargs):
    sender = KafkaWorkflowCommunicationReceiver(
        config.WORKFLOW_COMMUNICATION_KAFKA_CONFIG,
        *_get_kafka_configs(config, protocol_translation)
    )
    return sender


def _get_kafka_configs(config, protocol_translation):
    try:
        protocol = protocol_translation[config.WORKFLOW_COMMUNICATION_PROTOCOL]
    except KeyError:
        message = 'Could not find communication protocol {}'.format(config.WORKFLOW_COMMUNICATION_PROTOCOL)
        logger.error(message)
        raise ValueError(message)
    kafka_config = config.WORKFLOW_COMMUNICATION_KAFKA_CONFIG
    try:
        workflow_topic = kafka_config.pop('workflow_communication_topic')
    except KeyError:
        message = "'workflow_communication_topic' must be provided in kafka configuration"
        logger.error(message)
        raise ValueError(message)
    try:
        case_topic = kafka_config.pop('case_communication_topic')
    except KeyError:
        message = "'case_communication_topic' must be provided in kafka configuration"
        logger.error(message)
        raise ValueError(message)
    return workflow_topic, case_topic, protocol


_transportation_translation = {
    'zmq': (make_zmq_communication_sender, make_zmq_communication_receiver),
    'kafka': (make_kafka_communication_sender, make_kafka_communication_receiver)
}

_protocol_translation = {
    'protobuf': ProtobufWorkflowCommunicationConverter
}


def make_communication_sender(
        config,
        transportation_translation=_transportation_translation,
        protocol_translation=_protocol_translation,
        **init_options
):
    return _make_communication_handler(
        'sender',
        config,
        transportation_translation=transportation_translation,
        protocol_translation=protocol_translation,
        **init_options)


def make_communication_receiver(
        config,
        transportation_translation=_transportation_translation,
        protocol_translation=_protocol_translation,
        **init_options
):
    return _make_communication_handler(
        'receiver',
        config,
        transportation_translation=transportation_translation,
        protocol_translation=protocol_translation,
        **init_options)


def _make_communication_handler(
        handler_type,
        config,
        transportation_translation=_transportation_translation,
        protocol_translation=_protocol_translation,
        **kwargs
):
    handler_index = 0 if handler_type == 'sender' else 1
    try:
        handler = config.WORKFLOW_COMMUNICATION_HANDLER
        return transportation_translation[handler][handler_index](config, protocol_translation, **kwargs)
    except KeyError:
        message = 'Could not find communication transportation {}'.format(handler)
        logger.error(message)
        raise ValueError(message)
