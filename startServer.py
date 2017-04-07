from gevent import ssl
from os.path import isfile
from gevent.wsgi import WSGIServer
import core.case.database as case_database
from core.config import config, paths
from server import flaskServer


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
            flaskServer.displayIfFileNotFound(paths.certificate_path)
            flaskServer.displayIfFileNotFound(paths.private_key_path)
    return None


if __name__ == "__main__":
    case_database.initialize()
    ssl_context = get_ssl_context()
    try:
        port = int(config.port)
        host = config.host
        if ssl_context:
            server = WSGIServer((host, port), application=flaskServer.app, ssl_context=ssl_context)
            print('Listening on host https://' + host + ':' + str(port))
        else:
            server = WSGIServer((host, port), application=flaskServer.app)
            print('Listening on host http://'+host+':'+str(port))
        server.serve_forever()
    except ValueError:
        print('Invalid port {0}. Port must be an integer'.format(config.port))
