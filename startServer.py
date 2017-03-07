import ssl
from os.path import isfile
from gevent.wsgi import WSGIServer
import core.case.database as case_database
from core import config
from server import flaskServer

def get_ssl_context():
    if config.https.lower() == "true":
        # Sets up HTTPS
        if config.TLS_version == "1.2":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        elif config.TLS_version == "1.1":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        if isfile(config.certificatePath) and isfile(config.privateKeyPath):
            context.load_cert_chain(config.certificatePath, config.privateKeyPath)
            return context
        else:
            flaskServer.displayIfFileNotFound(config.certificatePath)
            flaskServer.displayIfFileNotFound(config.privateKeyPath)
    return None


if __name__ == "__main__":
    case_database.initialize()
    ssl_context = get_ssl_context()
    try:
        port = int(config.port)
        host = config.host
        if ssl_context:
            server = WSGIServer((host, port), application=flaskServer.app, ssl_context=ssl_context)
        else:
            server = WSGIServer((host, port), application=flaskServer.app)
        print('Listening on host '+host+' and port '+str(port)+'...')
        server.serve_forever()
    except ValueError:
        print('Invalid port {0}. Port must be an integer'.format(config.port))
