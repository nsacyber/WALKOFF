import threading

import walkoff.config
from walkoff.multiprocessedexecutor.kafka_receivers import KafkaWorkflowResultsReceiver

if __name__ == '__main__':
    walkoff.config.initialize()

    receiver = KafkaWorkflowResultsReceiver()
    receiver_thread = threading.Thread(target=receiver.receive_results)
    receiver_thread.start()
