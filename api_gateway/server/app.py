import logging
import os
import sys
import json

import connexion
from flask import Blueprint
from flask_swagger_ui import get_swaggerui_blueprint
from healthcheck import HealthCheck
from jinja2 import FileSystemLoader
from yaml import Loader, load

from sqlalchemy import event
from api_gateway.executiondb.workflow import Workflow

import api_gateway.config
from api_gateway.extensions import db, jwt
from api_gateway.server import context
from api_gateway.helpers import compose_api
from api_gateway.server.blueprints import console, root
from api_gateway.server.endpoints.results import results_stream
from common.elasticsearch_helpers import connect_to_elasticsearch
from common.init_containers import init_elasticsearch

logger = logging.getLogger(__name__)


def register_blueprints(flaskapp):
    flaskapp.logger.info('Registering builtin blueprints')
    flaskapp.register_blueprint(results_stream, url_prefix='/api/streams/workflowqueue')
    flaskapp.register_blueprint(console.console_stream, url_prefix='/api/streams/console')
    flaskapp.register_blueprint(root.root_page, url_prefix='/')
    for blueprint in (results_stream, console.console_stream):
        blueprint.cache = flaskapp.running_context.cache


def __get_blueprints_in_module(module):
    blueprints = [getattr(module, field)
                  for field in dir(module) if (not field.startswith('__')
                                               and isinstance(getattr(module, field), Blueprint))]
    return blueprints


def __register_blueprint(flaskapp, blueprint, url_prefix):
    url_prefix = f'{url_prefix}{blueprint.url_suffix}' if blueprint.url_suffix else url_prefix
    blueprint.url_prefix = url_prefix
    flaskapp.register_blueprint(blueprint, url_prefix=url_prefix)
    flaskapp.logger.info(f'Registered custom interface blueprint at url prefix {url_prefix}')


def register_swagger_blueprint(flaskapp):
    # register swagger API docs location
    swagger_path = os.path.join(api_gateway.config.Config.API_PATH, 'composed_api.yaml')
    swagger_yaml = load(open(swagger_path), Loader=Loader)
    swaggerui_blueprint = get_swaggerui_blueprint(api_gateway.config.Config.SWAGGER_URL, swagger_yaml,
                                                  config={'spec': swagger_yaml})
    flaskapp.register_blueprint(swaggerui_blueprint, url_prefix=api_gateway.config.Config.SWAGGER_URL)
    flaskapp.logger.info("Registered blueprint for swagger API docs at url prefix /api/docs")


def add_health_check(_app):
    health = HealthCheck(_app, '/health')
    from api_gateway.server.endpoints.health import checks
    for check in checks:
        health.add_check(check)


# Create the app on import and allow access to main app anywhere in program
connexion_app = connexion.App(__name__, specification_dir='../api/', options={'swagger_ui': False})
_app = connexion_app.app

_app.jinja_loader = FileSystemLoader([os.path.join("api_gateway", "templates")])
_app.config.from_object(api_gateway.config.Config)

try:
    db.init_app(_app)
except Exception as e:
    logger.error("Error initializing walkoff database. Please make sure all settings are properly configured in the"
                 "config file, and that all necessary environment variables are set correctly."
                 f"Error message: {str(e)}")
    sys.exit(1)

jwt.init_app(_app)
compose_api(api_gateway.config.Config)
connexion_app.add_api('composed_api.yaml')
_app.running_context = context.Context(app=_app)
register_blueprints(_app)
register_swagger_blueprint(_app)

add_health_check(_app)


# Validate database models before saving them, here.
# This is here to avoid circular imports.
with _app.app_context():
    @event.listens_for(_app.running_context.execution_db.session, "before_flush")
    def validate_before_flush(session, flush_context, instances):
        for instance in session.dirty:
            if isinstance(instance, Workflow):
                instance.validate()


@_app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


with open('api_gateway/server/es_index.json') as f:
    init_elasticsearch()
    es = connect_to_elasticsearch()
    es.indices.create(index='walkoff_results_index', body=json.load(f))
    logger.info(f"Was ES index creation successful? {es.indices.exists('walkoff_results_index')}")

app = _app



