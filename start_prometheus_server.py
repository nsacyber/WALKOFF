from flask import Flask
from werkzeug.wsgi import DispatcherMiddleware
from prometheus_client import make_wsgi_app


if __name__ == "__main__":
    app = Flask(__name__)

    app_dispatch = DispatcherMiddleware(app, {
        '/prometheus_metrics': make_wsgi_app()
    })
