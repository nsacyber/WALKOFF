import logging
import os
import uuid

import gevent
import zmq.auth
from zmq import ZMQError, green as zmq

from walkoff.events import WalkoffEvent
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb.workflow import Workflow
from walkoff.multiprocessedexecutor.protoconverter import ProtobufWorkflowResultsConverter

logger = logging.getLogger(__name__)


class ZmqWorkflowResultsSender(object):
    def __init__(self, socket_id, client_secret_key, client_public_key, server_public_key, zmq_results_address,
                 execution_db, case_logger, message_converter=ProtobufWorkflowResultsConverter):
        """Initialize a WorkflowResultsHandler object, which will be sending results of workflow execution

        Args:
            socket_id (str): The ID for the results socket
            client_secret_key (str): The secret key for the client
            client_public_key (str): The public key for the client
            server_public_key (str): The public key for the server
            zmq_results_address (str): The address for the ZMQ results socket
            execution_db (ExecutionDatabase): An ExecutionDatabase connection object
            case_logger (CaseLoger): A CaseLogger instance
        """
        self.results_sock = zmq.Context().socket(zmq.PUSH)
        self.results_sock.identity = socket_id
        self.results_sock.curve_secretkey = client_secret_key
        self.results_sock.curve_publickey = client_public_key
        self.results_sock.curve_serverkey = server_public_key
        try:
            self.results_sock.connect(zmq_results_address)
        except ZMQError:
            logger.exception('Workflow Results handler could not connect to {}!'.format(zmq_results_address))
            raise

        self.message_converter = message_converter
        self.execution_db = execution_db

        self.case_logger = case_logger

    def shutdown(self):
        """Shuts down the results socket and tears down the ExecutionDatabase
        """
        self.results_sock.close()
        self.execution_db.tear_down()

    def handle_event(self, workflow, sender, **kwargs):
        """Listens for the data_sent callback, which signifies that an execution element needs to trigger a
                callback in the main thread.

            Args:
                workflow (Workflow): The Workflow object that triggered the event
                sender (ExecutionElement): The execution element that sent the signal.
                kwargs (dict): Any extra data to send.
        """
        event = kwargs['event']
        if event in [WalkoffEvent.TriggerActionAwaitingData, WalkoffEvent.WorkflowPaused]:
            saved_workflow = SavedWorkflow.from_workflow(workflow)
            self.execution_db.session.add(saved_workflow)
            self.execution_db.session.commit()
        elif kwargs['event'] == WalkoffEvent.ConsoleLog:
            action = workflow.get_executing_action()
            sender = action

        packet_bytes = self.message_converter.event_to_protobuf(sender, workflow, **kwargs)
        self.case_logger.log(event, sender.id, kwargs.get('data', None))
        self.results_sock.send(packet_bytes)


class KafkaWorkflowResultsSender(object):
    def __init__(
            self,
            config,
            execution_db,
            case_logger,
            workflow_event_topic,
            message_converter=ProtobufWorkflowResultsConverter
    ):
        try:
            from comfluent_kafka import Producer
        except ImportError:
            logger.fatal('Could not import Kafka Producer. Try pip install confluent-kafka')
            raise
        self.producer = Producer(config)
        self.execution_db = execution_db
        self.case_logger = case_logger
        self.topic = workflow_event_topic
        self.message_converter = message_converter

    def shutdown(self):
        self.producer.flush()

    @staticmethod
    def _delivery_callback(err, msg):
        if err is not None:
            logger.error('Kafka message delivery failed: {}'.format(err))

    def _format_topic(self, event):
        return '{}.{}'.format(self.topic, event.name)

    def handle_event(self, workflow, sender, **kwargs):
        """Listens for the data_sent callback, which signifies that an execution element needs to trigger a
                callback in the main thread.

            Args:
                workflow (Workflow): The Workflow object that triggered the event
                sender (ExecutionElement): The execution element that sent the signal.
                kwargs (dict): Any extra data to send.
        """
        event = kwargs['event']
        if event in [WalkoffEvent.TriggerActionAwaitingData, WalkoffEvent.WorkflowPaused]:
            saved_workflow = SavedWorkflow.from_workflow(workflow)
            self.execution_db.session.add(saved_workflow)
            self.execution_db.session.commit()
        elif event == WalkoffEvent.ConsoleLog:
            action = workflow.get_executing_action()
            sender = action

        packet_bytes = self.message_converter.event_to_protobuf(sender, workflow, **kwargs)
        self.producer.produce(
            self._format_topic(event),
            packet_bytes,
            key=str(workflow.id),
            callback=self._delivery_callback
        )
        if event.is_loggable():
            self.case_logger.log(event, sender.id, kwargs.get('data', None))


class ZmqWorkflowResultsReceiver:
    def __init__(
            self,
            server_secret,
            server_public,
            address,
            current_app,
            message_converter=ProtobufWorkflowResultsConverter
    ):
        """Initialize a Receiver object, which will receive callbacks from the ExecutionElements.

        Args:
            current_app (Flask.App): The current Flask app
        """
        self.message_converter = message_converter
        self.thread_exit = False
        self.workflows_executed = 0

        # server_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        # server_public, server_secret = auth.load_certificate(server_secret_file)

        ctx = zmq.Context.instance()
        self.results_sock = ctx.socket(zmq.PULL)
        self.results_sock.curve_secretkey = server_secret
        self.results_sock.curve_publickey = server_public
        self.results_sock.curve_server = True
        # self.results_sock.bind(walkoff.config.Config.ZMQ_RESULTS_ADDRESS)
        self.results_sock.bind(address)
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
        event, sender, data = self.message_converter.to_event_callback(message_bytes)
        if sender is not None:
            with self.current_app.app_context():
                event.send(sender, data=data)
            if event in [WalkoffEvent.WorkflowShutdown, WalkoffEvent.WorkflowAborted]:
                self._increment_execution_count()

    def _increment_execution_count(self):
        self.workflows_executed += 1


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
