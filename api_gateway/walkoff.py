from gevent import monkey
monkey.patch_all()

import argparse
import logging
import os
import sys
import traceback

from gevent import pywsgi

import api_gateway
import api_gateway.config
from api_gateway.jsonplaybookloader import JsonPlaybookLoader
# from api_gateway.executiondb.playbook import Playbook
from api_gateway.helpers import compose_api
from api_gateway.server.app import app

logger = logging.getLogger('API-GATEWAY')


def run(host, port):
    print_banner()
    server = setup_server(host, port)
    server.serve_forever()


def print_banner():
    banner = '***** Running WALKOFF v.{} *****'.format(api_gateway.__version__)
    header_footer_banner = '*' * len(banner)
    logger.info(header_footer_banner)
    logger.info(banner)
    logger.info(header_footer_banner)


def setup_server(host, port):
    if os.path.isfile(api_gateway.config.Config.CERTIFICATE_PATH) and os.path.isfile(
            api_gateway.config.Config.PRIVATE_KEY_PATH):
        server = pywsgi.WSGIServer((host, port), application=app,
                                   keyfile=api_gateway.config.Config.PRIVATE_KEY_PATH,
                                   certfile=api_gateway.config.Config.CERTIFICATE_PATH)
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
    parser.add_argument('-a', '--apponly', help='start WALKOFF app only, no workers', action='store_true')
    args = parser.parse_args()
    if args.version:
        print(api_gateway.__version__)
        exit(0)

    return args


def convert_host_port(args):
    host = api_gateway.config.Config.HOST if args.host is None else args.host
    port = api_gateway.config.Config.PORT if args.port is None else args.port
    try:
        port = int(port)
    except ValueError:
        print('Invalid port {}. Port must be an integer!'.format(port))
        exit(1)
    return host, port


# def import_workflows():
#     playbook_name = [playbook._id for playbook in app.running_context.execution_db.session.query(Playbook).all()]
#     if os.path.exists(api_gateway.config.Config.WORKFLOWS_PATH):
#         logger.info('Importing any workflows not currently in database')
#         for p in os.listdir(api_gateway.config.Config.WORKFLOWS_PATH):
#             full_path = os.path.join(api_gateway.config.Config.WORKFLOWS_PATH, p)
#             if os.path.isfile(full_path):
#                 playbook = JsonPlaybookLoader.load_playbook(full_path)
#                 if playbook.name not in playbook_name:
#                     app.running_context.execution_db.session.add(playbook)
#         app.running_context.execution_db.session.commit()


if __name__ == "__main__":
    args = parse_args()
    exit_code = 0
    api_gateway.config.initialize(args.config)

    # import_workflows()
    try:
        run(*convert_host_port(args))
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt! Please wait a few seconds for WALKOFF to shutdown.')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exc()
        exit_code = 1
    finally:
        logger.info('Shutting down server')
        sys.exit(exit_code)
