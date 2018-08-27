import logging
import os
import uuid

logger = logging.getLogger(__name__)


def make_zmq_workflow_results_sender(config, execution_db, case_logger, protocol_translation, **kwargs):
    try:
        protocol = protocol_translation[config.WORKFLOW_COMMUNICATION_PROTOCOL]
    except KeyError:
        message = 'Could not find communication protocol {}'.format(config.WORKFLOW_COMMUNICATION_PROTOCOL)
        logger.error(message)
        raise ValueError(message)
    else:
        server_secret_file = os.path.join(config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public_key, _server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(config.ZMQ_PRIVATE_KEYS_PATH, "client.key_secret")
        client_public_key, client_secret_key = auth.load_certificate(client_secret_file)
        address = config.ZMQ_RESULTS_ADDRESS

        return ZmqWorkflowResultsSender(
            'Workflow_Results_Sender_{}'.format(kwargs.get('id', uuid.uuid4())),
            client_secret_key,
            client_public_key,
            server_public_key,
            address,
            execution_db,
            case_logger,
            message_converter=protocol
        )


def make_zmq_workflow_results_receiver(config, protocol_translation, **kwargs):
    try:
        protocol = protocol_translation[config.WORKFLOW_COMMUNICATION_PROTOCOL]
    except KeyError:
        message = 'Could not find communication protocol {}'.format(config.WORKFLOW_COMMUNICATION_PROTOCOL)
        logger.error(message)
        raise ValueError(message)
    else:
        server_secret_file = os.path.join(config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)
        address = config.ZMQ_RESULTS_ADDRESS

        return ZmqWorkflowResultsReceiver(
            server_secret,
            server_public,
            address,
            kwargs['current_app'],
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
