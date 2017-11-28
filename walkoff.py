import logging.config
import sys, traceback
import ssl
import os
from os.path import isfile
from core.config import config, paths
from apps import *
from gevent.wsgi import WSGIServer
from gevent import monkey

logger = logging.getLogger('walkoff')


def get_ssl_context():
    if config.https:
        # Sets up HTTPS
        if config.tls_version == "1.2":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        elif config.tls_version == "1.1":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        if isfile(paths.certificate_path) and isfile(paths.private_key_path):
            context.load_cert_chain(paths.certificate_path, paths.private_key_path)
            return context
        else:
            print('Certificates not found')
    return None


def setup_logger():
    log_config = None
    if isfile(paths.logging_config_path):
        try:
            with open(paths.logging_config_path, 'rt') as log_config_file:
                log_config = json.loads(log_config_file.read())
        except:
            print('Invalid JSON in logging config file')
            pass
    else:
        print('No logging config found')

    if log_config is not None:
        logging.config.dictConfig(log_config)
    else:
        logging.basicConfig()
        logger.info("Basic logging is being used")


def run():
    from core.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
    setup_logger()
    pids = spawn_worker_processes()
    monkey.patch_all()
    from server import flaskserver
    flaskserver.running_context.controller.initialize_threading(pids=pids)
    # The order of these imports matter for initialization (should probably be fixed)
    from compose_api import compose_api
    compose_api()

    import core.case.database as case_database
    case_database.initialize()
    ssl_context = get_ssl_context()

    try:
        port = int(config.port)
    except ValueError:
        print('Invalid port {0}. Port must be an integer'.format(config.port))
    else:
        host = config.host
        if ssl_context:
            server = WSGIServer((host, port), application=flaskserver.app, ssl_context=ssl_context)
            proto = 'https'
        else:
            server = WSGIServer((host, port), application=flaskserver.app)
            proto = 'http'
        from core.config.config import walkoff_version
        logger.info('*** Running WALKOFF v.{} ***'.format(walkoff_version))
        logger.info('Listening on host {0}://{1}:{2}'.format(proto, host, port))

        server.serve_forever()

        # app.run()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt!')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exc()
    finally:
        from server import flaskserver

        flaskserver.running_context.controller.shutdown_pool()
        logger.info('Shutting down server')
        os._exit(0)
