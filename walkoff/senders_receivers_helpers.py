import logging

import walkoff.config
from walkoff.multiprocessedexecutor.kafka_receivers import make_kafka_results_receiver
from walkoff.multiprocessedexecutor.kafka_senders import make_kafka_results_sender, make_kafka_communication_sender
from walkoff.multiprocessedexecutor.protoconverter import ProtobufWorkflowCommunicationConverter
from walkoff.multiprocessedexecutor.zmq_receivers import make_zmq_results_receiver
from walkoff.multiprocessedexecutor.zmq_senders import make_zmq_results_sender, make_zmq_communication_sender
from walkoff.worker.kafka_workflow_receivers import make_kafka_communication_receiver
from walkoff.worker.zmq_workflow_receivers import make_zmq_communication_receiver

logger = logging.getLogger(__name__)

_results_transportation_translation = {'zmq': (make_zmq_results_sender, make_zmq_results_receiver),
                                       'kafka': (make_kafka_results_sender, make_kafka_results_receiver)}

_comm_transportation_translation = {'zmq': (make_zmq_communication_sender, make_zmq_communication_receiver),
                                    'kafka': (make_kafka_communication_sender, make_kafka_communication_receiver)}

_protocol_translation = {'protobuf': ProtobufWorkflowCommunicationConverter}


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
