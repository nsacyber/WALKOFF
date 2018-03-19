import argparse
import json
import logging.config
import os
import sys
import traceback
import warnings
from os.path import isfile

from gevent import monkey
from gevent import pywsgi

import walkoff
import walkoff.cache
import walkoff.config

logger = logging.getLogger('walkoff')


def setup_logger():
    log_config = None
    if isfile(walkoff.config.Config.LOGGING_CONFIG_PATH):
        try:
            with open(walkoff.config.Config.LOGGING_CONFIG_PATH, 'rt') as log_config_file:
                log_config = json.loads(log_config_file.read())
        except (IOError, OSError):
            print('Could not read logging JSON file {}'.format(walkoff.config.Config.LOGGING_CONFIG_PATH))
        except ValueError:
            print('Invalid JSON in logging config file')
    else:
        print('No logging config found')

    if log_config is not None:
        logging.config.dictConfig(log_config)
    else:
        logging.basicConfig()
        logger.info("Basic logging is being used")

    def send_warnings_to_log(message, category, filename, lineno, file=None):
        logging.warning(
            '%s:%s: %s:%s' %
            (filename, lineno, category.__name__, message))
        return

    warnings.showwarning = send_warnings_to_log


def run(host, port):
    from walkoff.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
    setup_logger()
    print_banner()
    pids = spawn_worker_processes(walkoff.config.Config.NUMBER_PROCESSES,
                                  walkoff.config.Config.NUM_THREADS_PER_PROCESS,
                                  walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH,
                                  walkoff.config.Config.ZMQ_RESULTS_ADDRESS,
                                  walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS)
    monkey.patch_all()

    from scripts.compose_api import compose_api
    compose_api()

    from walkoff.server import flaskserver
    flaskserver.running_context.executor.initialize_threading(walkoff.config.Config.ZMQ_PUBLIC_KEYS_PATH,
                                                              walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH,
                                                              walkoff.config.Config.ZMQ_RESULTS_ADDRESS,
                                                              walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS,
                                                              pids)
    # The order of these imports matter for initialization (should probably be fixed)

    import walkoff.case.database as case_database
    case_database.initialize()

    server = setup_server(flaskserver.app, host, port)
    server.serve_forever()


def print_banner():
    banner = '***** Running WALKOFF v.{} *****'.format(walkoff.__version__)
    header_footer_banner = '*' * len(banner)
    logger.info(header_footer_banner)
    logger.info(banner)
    logger.info(header_footer_banner)


def setup_server(app, host, port):
    if isfile(walkoff.config.Config.CERTIFICATE_PATH) and isfile(walkoff.config.Config.PRIVATE_KEY_PATH):
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


def connect_to_cache():
    walkoff.cache.cache = walkoff.cache.make_cache(walkoff.config.Config.CACHE_CONFIG)


if __name__ == "__main__":
    args = parse_args()
    exit_code = 0
    try:
        walkoff.config.initialize()
        connect_to_cache()
        from walkoff import initialize_databases

        initialize_databases()
        run(*convert_host_port(args))
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt!')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exc()
        exit_code = 1
    finally:
        from walkoff.server import flaskserver

        flaskserver.running_context.executor.shutdown_pool()
        logger.info('Shutting down server')
        os._exit(exit_code)
