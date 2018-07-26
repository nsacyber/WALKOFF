import click

import logging
import os
import sys
import traceback

from gevent import monkey
from gevent import pywsgi

import walkoff
import walkoff.config
from scripts.compose_api import compose_api
from walkoff.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
from walkoff.server.app import create_app
from tests.util.jsonplaybookloader import JsonPlaybookLoader
from walkoff.executiondb.playbook import Playbook

logger = logging.getLogger('walkoff')


@click.command()
@click.option(
    '-H',
    '--host',
    help='The host address to use for the Walkoff server. Defaults to setting contained in ./data/walkoff.config'
)
@click.option(
    '-p',
    '--port',
    help='The port to use for the Walkoff server. Defaults to setting contained in ./data/walkoff.config',
    type=int
)
@click.option(
    '-c',
    '--config',
    help=('Specify the path to the configuration to use for running the Walkoff instance. '
          'Defaults to ./data/walkoff.config')
)
@click.pass_context
def run(ctx, host, port, config):
    """Main entry point to run Walkoff locally.

    This command starts a Walkoff server locally. If run from the directory of a locally-installed Walkoff instance it
    will use the configuration file located in ./data/walkoff.config, otherwise you can specify the path to the
    configuration using the --config option.

    This local install is intended for testing purposes only, and it is recommended that you use the kubernetes version.
    """
    exit_code = 0
    compose_api()
    walkoff.config.initialize(config)
    app = create_app(walkoff.config.Config)
    import_workflows(app)
    try:
        _run_server(app, *convert_host_port(host, port))
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



def _run_server(app, host, port):
    print_banner()
    pids = spawn_worker_processes()
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


def convert_host_port(host, port):
    host = walkoff.config.Config.HOST if host is None else host
    port = walkoff.config.Config.PORT if port is None else port
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
