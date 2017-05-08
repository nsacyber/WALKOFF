import logging.config
from gevent import ssl
from os.path import isfile
import json
from gevent.wsgi import WSGIServer
import core.case.database as case_database
from core.config import config, paths
from server import flaskserver

logger = logging.getLogger('startserver')

def get_ssl_context():
    if config.https.lower() == "true":
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
            flaskserver.display_if_file_not_found(paths.certificate_path)
            flaskserver.display_if_file_not_found(paths.private_key_path)
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


if __name__ == "__main__":
    case_database.initialize()
    ssl_context = get_ssl_context()
    flaskserver.running_context.init_threads()
    try:
        port = int(config.port)
    except ValueError:
        print('Invalid port {0}. Port must be an integer'.format(config.port))
    else:
        host = config.host
        if ssl_context:
            server = WSGIServer((host, port), application=flaskserver.app, ssl_context=ssl_context)

        else:
            server = WSGIServer((host, port), application=flaskserver.app)
        setup_logger()
        logger.info('Listening on host https://{0}:{1}'.format(host, port))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info('Shutting down server')
