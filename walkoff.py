import argparse
import logging
import os
import sys
import traceback

from gevent import monkey
from gevent import pywsgi
from prometheus_flask_exporter import PrometheusMetrics

import walkoff
import walkoff.config
from tests.util.jsonplaybookloader import JsonPlaybookLoader
from walkoff.executiondb.playbook import Playbook
from walkoff.helpers import compose_api
from walkoff.server.app import create_app

logger = logging.getLogger('walkoff')


def run(args, app, host, port):
    print_banner()
    if not args.apponly:
        from start_workers import spawn_worker_processes
        pids = spawn_worker_processes()
    else:
        pids = None

    monkey.patch_all()

    app.running_context.inject_app(app)
    app.running_context.executor.initialize_threading(app, pids)
    # The order of these imports matter for initialization (should probably be fixed)

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
    parser.add_argument('-a', '--apponly', help='start WALKOFF app only, no workers', action='store_true')
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


def import_workflows(app):
    playbook_name = [playbook.id for playbook in app.running_context.execution_db.session.query(Playbook).all()]
    if os.path.exists(walkoff.config.Config.WORKFLOWS_PATH):
        logger.info('Importing any workflows not currently in database')
        for p in os.listdir(walkoff.config.Config.WORKFLOWS_PATH):
            full_path = os.path.join(walkoff.config.Config.WORKFLOWS_PATH, p)
            if os.path.isfile(full_path):
                playbook = JsonPlaybookLoader.load_playbook(full_path)
                if playbook.name not in playbook_name:
                    app.running_context.execution_db.session.add(playbook)
        app.running_context.execution_db.session.commit()


if __name__ == "__main__":
    args = parse_args()
    exit_code = 0
    walkoff.config.initialize(args.config)
    compose_api(walkoff.config.Config)
    app = create_app()

    if not walkoff.config.Config.SEPARATE_PROMETHEUS:
        metrics = PrometheusMetrics(app, path='/prometheus_metrics')

    import_workflows(app)
    try:
        run(args, app, *convert_host_port(args))
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt! Please wait a few seconds for WALKOFF to shutdown.')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exc()
        exit_code = 1
    finally:
        app.running_context.executor.shutdown_pool()
        logger.info('Shutting down server')
        os._exit(exit_code)
