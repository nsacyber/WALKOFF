import logging

from os import path

import importlib
import connexion
from flask import Blueprint
from jinja2 import FileSystemLoader

from walkoff.interfacebase import AppBlueprint
import walkoff.config
from walkoff.extensions import db, jwt
from walkoff.helpers import import_submodules
from walkoff.server import context
from walkoff.server.blueprints import custominterface, workflowresults, notifications, console, root

logger = logging.getLogger(__name__)


def register_blueprints(flaskapp):
    flaskapp.logger.info('Registering builtin blueprints')
    flaskapp.register_blueprint(custominterface.custom_interface_page, url_prefix='/custominterfaces/<interface>')
    flaskapp.register_blueprint(workflowresults.workflowresults_page, url_prefix='/api/streams/workflowqueue')
    flaskapp.register_blueprint(notifications.notifications_page, url_prefix='/api/streams/messages')
    flaskapp.register_blueprint(console.console_page, url_prefix='/api/streams/console')
    flaskapp.register_blueprint(root.root_page, url_prefix='/')
    for blueprint in (workflowresults.workflowresults_page, notifications.notifications_page, console.console_page):
        blueprint.cache = flaskapp.running_context.cache
    __register_all_app_blueprints(flaskapp)


def __get_blueprints_in_module(module):
    blueprints = [getattr(module, field)
                  for field in dir(module) if (not field.startswith('__')
                                               and isinstance(getattr(module, field), Blueprint))]
    return blueprints


def __register_blueprint(flaskapp, blueprint, url_prefix):
    if isinstance(blueprint, AppBlueprint):
        blueprint.cache = flaskapp.running_context.cache
    url_prefix = '{0}{1}'.format(url_prefix, blueprint.url_suffix) if blueprint.url_suffix else url_prefix
    blueprint.url_prefix = url_prefix
    flaskapp.register_blueprint(blueprint, url_prefix=url_prefix)
    flaskapp.logger.info('Registered custom interface blueprint at url prefix {}'.format(url_prefix))


def __register_app_blueprints(flaskapp, app_name, blueprints):
    url_prefix = '/interfaces/{0}'.format(app_name.split('.')[-1])
    for blueprint in blueprints:
        __register_blueprint(flaskapp, blueprint, url_prefix)


def __register_all_app_blueprints(flaskapp):
    from walkoff.helpers import import_submodules
    interfaces_dir, interfaces_pkg = path.split(walkoff.config.Config.INTERFACES_PATH)
    ext_interfaces = importlib.import_module(interfaces_pkg)
    imported_apps = import_submodules(ext_interfaces)
    for interface_name, interfaces_module in imported_apps.items():
        try:
            interface_blueprints = []
            for submodule in import_submodules(interfaces_module, recursive=True).values():
                interface_blueprints.extend(__get_blueprints_in_module(submodule))
        except ImportError:
            pass
        else:
            __register_app_blueprints(flaskapp, interface_name, interface_blueprints)


def create_app(app_config):
    connexion_app = connexion.App(__name__)
    _app = connexion_app.app
    _app.jinja_loader = FileSystemLoader([walkoff.config.Config.TEMPLATES_PATH])
    _app.config.from_object(app_config)

    db.init_app(_app)
    jwt.init_app(_app)
    connexion_app.add_api(walkoff.config.Config.API_PATH)

    _app.running_context = context.Context(walkoff.config.Config)
    register_blueprints(_app)

    return _app
