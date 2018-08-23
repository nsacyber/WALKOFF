from confluent_kafka.cimpl import Producer

from walkoff.events import WalkoffEvent
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.multiprocessedexecutor.protoconverter import ProtobufWorkflowResultsConverter as ProtoConverter, \
    ProtobufWorkflowCommunicationConverter
import logging

logger = logging.getLogger(__name__)


class KafkaWorkflowResultsSender(object):
    def __init__(self, config, execution_db, workflow_event_topic, message_converter=ProtoConverter):
        self.producer = Producer(config)
        self.execution_db = execution_db
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
        self.producer.produce(self._format_topic(event), packet_bytes, key=str(workflow.id),
                              callback=self._delivery_callback)


class KafkaWorkflowCommunicationSender(object):
    _requires = ['confluent-kafka']

    def __init__(self, config, workflow_communication_topic, message_converter=ProtobufWorkflowCommunicationConverter):
        self.producer = Producer(config)
        self.workflow_communication_topic = workflow_communication_topic
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
        self.producer.produce(topic, message, key=key, callback=self._delivery_callback)


def make_kafka_communication_sender(config, protocol_translation, **kwargs):
    sender = KafkaWorkflowCommunicationSender(config.WORKFLOW_COMMUNICATION_KAFKA_CONFIG,
                                              *_get_kafka_configs(config, protocol_translation))
    return sender