import argparse
import logging
import os
import sys
import threading
import traceback

from gevent import monkey, pywsgi

import walkoff.cache
import walkoff.config
from walkoff.senders_receivers_helpers import make_results_receiver
from walkoff.server.app import create_app

logger = logging.getLogger(__name__)


def run(app, host, port):
    print_banner()

    monkey.patch_all()

    server = setup_server(app, host, port)
    server.serve_forever()


def print_banner():
    banner = '***** Running WALKOFF v.{} *****'.format(walkoff.__version__)
    header_footer_banner = '*' * len(banner)
    logger.info(header_footer_banner)
    logger.info(banner)
    logger.info(header_footer_banner)


def setup_server(app, host, port):
    if os.path.isfile(walkoff.config.Config.CERTIFICATE_PATH) and os.path.isfile(
            walkoff.config.Config.PRIVATE_KEY_PATH):
        server = pywsgi.WSGIServer((host, port), application=app,
                                   keyfile=walkoff.config.Config.PRIVATE_KEY_PATH,
                                   certfile=walkoff.config.Config.CERTIFICATE_PATH)
        protocol = 'https'
    else:
        logger.warning('Cannot find certificates. Using HTTP')
        server = pywsgi.WSGIServer((host, port), application=app)
        protocol = 'http'

    logger.info('Listening on host {0}://{1}:{2}'.format(protocol, host, port))
    return server


def parse_args():
    parser = argparse.ArgumentParser(description='Script to the WALKOFF server')
    parser.add_argument('-v', '--version', help='Get the version of WALKOFF running', action='store_true')
    parser.add_argument('-p', '--port', help='port to run the server on')
    parser.add_argument('-H', '--host', help='host address to run the server on')
    parser.add_argument('-c', '--config', help='configuration file to use')
    args = parser.parse_args()
    if args.version:
        print(walkoff.__version__)
        exit(0)

    return args


def convert_host_port(args):
    host = walkoff.config.Config.HOST if args.host is None else args.host
    port = walkoff.config.Config.PORT if args.port is None else args.port
    try:
        port = int(port)
    except ValueError:
        print('Invalid port {}. Port must be an integer!'.format(port))
        exit(1)
    return host, port


if __name__ == '__main__':
    exit_code = 0
    args = parse_args()

    walkoff.config.initialize(args.config)
    app = create_app()

    walkoff.config.Config.WORKFLOW_RESULTS_HANDLER = 'kafka'
    receiver = make_results_receiver()
    receiver_thread = threading.Thread(target=receiver.receive_results)
    receiver_thread.start()

    try:
        run(args, app, *convert_host_port(args))
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt! Please wait a few seconds for WALKOFF interface server to shutdown.')
        receiver.thread_exit = True
        receiver_thread.join(timeout=1)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exc()
        exit_code = 1
    finally:
        logger.info('Shutting down interface server')
        os._exit(0)
