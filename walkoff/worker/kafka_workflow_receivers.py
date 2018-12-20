import logging

from confluent_kafka import Consumer, KafkaError
from walkoff.multiprocessedexecutor.protoconverter import ProtobufWorkflowCommunicationConverter

import walkoff.config

logger = logging.getLogger(__name__)


class KafkaWorkflowCommunicationReceiver(object):
    """Receives communication via Kafka and sends it to the executing workflow"""
    _requires = ['confluent-kafka']

    def __init__(self, message_converter=ProtobufWorkflowCommunicationConverter):
        self._ready = False

        kafka_config = walkoff.config.Config.WORKFLOW_COMMUNICATION_KAFKA_CONFIG
        self.receiver = Consumer(kafka_config)
        self.topic = walkoff.config.Config.WORKFLOW_COMMUNICATION_KAFKA_TOPIC
        self.message_converter = message_converter
        self.exit = False

        if self.check_status():
            self._ready = True

    def shutdown(self):
        self.exit = True
        self.receiver.close()

    def receive_communications(self):
        """Constantly receives data from the Kafka and handles it accordingly"""
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

        return

    def is_ready(self):
        return self._ready

    def check_status(self):
        if self.receiver is not None:
            return True
        return False
