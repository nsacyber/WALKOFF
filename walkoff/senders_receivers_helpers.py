import logging

import walkoff.config
from walkoff.multiprocessedexecutor.kafka_receivers import KafkaWorkflowResultsReceiver
from walkoff.multiprocessedexecutor.kafka_senders import KafkaWorkflowResultsSender, KafkaWorkflowCommunicationSender
from walkoff.multiprocessedexecutor.protoconverter import ProtobufWorkflowCommunicationConverter, \
    ProtobufWorkflowResultsConverter
from walkoff.multiprocessedexecutor.zmq_receivers import ZmqWorkflowResultsReceiver
from walkoff.multiprocessedexecutor.zmq_senders import ZmqWorkflowResultsSender, ZmqWorkflowCommunicationSender
from walkoff.worker.kafka_workflow_receivers import KafkaWorkflowCommunicationReceiver
from walkoff.worker.zmq_workflow_receivers import ZmqWorkflowCommunicationReceiver

logger = logging.getLogger(__name__)


def make_kafka_results_receiver(**kwargs):
    if 'message_converter' in kwargs:
        msg_converter = kwargs['message_converter']
    else:
        msg_converter = _results_protocol_translation[walkoff.config.Config.WORKFLOW_RESULTS_PROTOCOL]
    return KafkaWorkflowResultsReceiver(msg_converter, kwargs.get('current_app', None))


def make_kafka_results_sender(**kwargs):
    if 'message_converter' in kwargs:
        msg_converter = kwargs['message_converter']
    else:
        msg_converter = _results_protocol_translation[walkoff.config.Config.WORKFLOW_RESULTS_PROTOCOL]
    return KafkaWorkflowResultsSender(kwargs['execution_db'], msg_converter, kwargs.get('socket_id', None))


def make_zmq_results_receiver(**kwargs):
    if 'message_converter' in kwargs:
        msg_converter = kwargs['message_converter']
    else:
        msg_converter = _results_protocol_translation[walkoff.config.Config.WORKFLOW_RESULTS_PROTOCOL]
    return ZmqWorkflowResultsReceiver(msg_converter, kwargs.get('current_app', None))


def make_zmq_results_sender(**kwargs):
    if 'message_converter' in kwargs:
        msg_converter = kwargs['message_converter']
    else:
        msg_converter = _results_protocol_translation[walkoff.config.Config.WORKFLOW_RESULTS_PROTOCOL]
    return ZmqWorkflowResultsSender(kwargs['execution_db'], msg_converter, kwargs.get('socket_id', None))


def make_kafka_communication_sender(**kwargs):
    if 'message_converter' in kwargs:
        msg_converter = kwargs['message_converter']
    else:
        msg_converter = _comm_protocol_translation[walkoff.config.Config.WORKFLOW_COMMUNICATION_PROTOCOL]
    return KafkaWorkflowCommunicationSender(msg_converter)


def make_zmq_communication_sender(**kwargs):
    if 'message_converter' in kwargs:
        msg_converter = kwargs['message_converter']
    else:
        msg_converter = _comm_protocol_translation[walkoff.config.Config.WORKFLOW_COMMUNICATION_PROTOCOL]
    return ZmqWorkflowCommunicationSender(msg_converter)


def make_kafka_communication_receiver(**kwargs):
    if 'message_converter' in kwargs:
        msg_converter = kwargs['message_converter']
    else:
        msg_converter = _comm_protocol_translation[walkoff.config.Config.WORKFLOW_COMMUNICATION_PROTOCOL]
    return KafkaWorkflowCommunicationReceiver(msg_converter)


def make_zmq_communication_receiver(**kwargs):
    if 'message_converter' in kwargs:
        msg_converter = kwargs['message_converter']
    else:
        msg_converter = _comm_protocol_translation[walkoff.config.Config.WORKFLOW_COMMUNICATION_PROTOCOL]
    return ZmqWorkflowCommunicationReceiver(kwargs['socket_id'], msg_converter)


_results_transportation_translation = {'zmq': (make_zmq_results_sender, make_zmq_results_receiver),
                                       'kafka': (make_kafka_results_sender, make_kafka_results_receiver)}

_comm_transportation_translation = {'zmq': (make_zmq_communication_sender, make_zmq_communication_receiver),
                                    'kafka': (make_kafka_communication_sender, make_kafka_communication_receiver)}

_results_protocol_translation = {'protobuf': ProtobufWorkflowResultsConverter}
_comm_protocol_translation = {'protobuf': ProtobufWorkflowCommunicationConverter}


def make_results_sender(**init_options):
    return _make_results_handler('sender', **init_options)


def make_results_receiver(**init_options):
    return _make_results_handler('receiver', **init_options)


def _make_results_handler(handler_type, **kwargs):
    handler_index = 0 if handler_type == 'sender' else 1
    handler = walkoff.config.Config.WORKFLOW_RESULTS_HANDLER
    try:
        return _results_transportation_translation[handler][handler_index](**kwargs)
    except KeyError:
        message = 'Could not find communication transportation {}'.format(handler)
        logger.error(message)
        raise ValueError(message)


def make_communication_sender(**init_options):
    return _make_communication_handler('sender', **init_options)


def make_communication_receiver(**init_options):
    return _make_communication_handler('receiver', **init_options)


def _make_communication_handler(handler_type, **kwargs):
    handler_index = 0 if handler_type == 'sender' else 1
    handler = walkoff.config.Config.WORKFLOW_COMMUNICATION_HANDLER
    try:
        return _comm_transportation_translation[handler][handler_index](**kwargs)
    except KeyError:
        message = 'Could not find communication transportation {}'.format(handler)
        logger.error(message)
        raise ValueError(message)
