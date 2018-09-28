import time

from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry
from flask import request
from walkoff.server.returncodes import *

FLASK_REQUEST_LATENCY = Histogram('flask_request_latency_seconds', 'Flask Request Latency',
                                  ['method', 'endppint'])
FLASK_REQUEST_COUNT = Counter('flask_request_count', 'Flask Request Count',
                              ['method', 'endpoint', 'http_status'])


def before_request():
    request.start_time = time.time()


def after_request(response):
    request_latency = time.time() - request.start_time
    FLASK_REQUEST_LATENCY.labels(request.method, request.path).observe(request_latency)
    FLASK_REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    return response


def setup_prometheus_monitoring(app):
    app.before_request(before_request)
    app.after_request(after_request)

    @app.route('/prometheus_metrics')
    def prometheus_metrics():
        print("prometheus metrics")
        registry = CollectorRegistry()
        return generate_latest(registry), SUCCESS
