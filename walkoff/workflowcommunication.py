import logging
import os
import uuid

import zmq.auth as auth
import zmq.green as zmq

logger = logging.getLogger(__name__)




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
