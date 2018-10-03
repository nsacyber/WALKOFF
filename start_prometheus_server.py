from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

import walkoff.config

if __name__ == "__main__":
    app = Flask('prometheus')
    PrometheusMetrics(app, path='/prometheus_metrics')
    app.run(host=walkoff.config.Config.HOST, port=walkoff.config.Config.PORT)
