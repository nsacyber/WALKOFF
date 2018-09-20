import argparse
import logging
import os
import threading

import walkoff.cache
import walkoff.config
from walkoff.senders_receivers_helpers import make_results_receiver
from walkoff.server.app import create_app

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

    walkoff.config.initialize(args.config)
    app = create_app(walkoff.config.Config)

    receiver = make_results_receiver()
    receiver_thread = threading.Thread(target=receiver.receive_results)
    receiver_thread.start()

    try:
        server = setup_server(app, host, port)
        server.serve_forever()
    except KeyboardInterrupt:
        receiver.thread_exit = True
        receiver_thread.join(timeout=1)
    finally:
        os._exit(0)
