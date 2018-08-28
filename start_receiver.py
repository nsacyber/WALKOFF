import argparse
import os
import logging
import walkoff.config
from walkoff.senders_receivers_helpers import make_results_receiver
import threading
import time

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Script to start WALKOFF Information Receiver')
    parser.add_argument('-v', '--version', help='Get the version of WALKOFF running', action='store_true')
    parser.add_argument('-c', '--config', help='Configuration file to use')
    args = parser.parse_args()
    if args.version:
        print(walkoff.__version__)
        exit(0)

    return args


if __name__ == '__main__':
    args = parse_args()

    if args.config:
        walkoff.config.initialize(args.config)

    receiver = make_results_receiver()
    receiver_thread = threading.Thread(target=receiver.receive_results)
    receiver_thread.start()

    try:
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        receiver.thread_exit = True
        receiver_thread.join(timeout=1)
    finally:
        os._exit(0)
