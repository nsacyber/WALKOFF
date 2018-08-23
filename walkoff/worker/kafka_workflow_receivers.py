from walkoff.multiprocessedexecutor.protoconverter import ProtobufWorkflowCommunicationConverter
from confluent_kafka import Consumer
import logging

logger = logging.getLogger(__name__)


class KafkaWorkflowCommunicationReceiver(object):
    _requires = ['confluent-kafka']

    def __init__(
            self,
            config,
            workflow_communication_topic,
            case_communication_topic,
            message_converter=ProtobufWorkflowCommunicationConverter
    ):
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


def make_kafka_communication_receiver(config, protocol_translation, **kwargs):
    sender = KafkaWorkflowCommunicationReceiver(
        config.WORKFLOW_COMMUNICATION_KAFKA_CONFIG,
        *_get_kafka_configs(config, protocol_translation)
    )
    return sender