import logging
import os

import connexion
from jinja2 import Environment, FileSystemLoader

import core.config.config
import server.database
from apps.devicedb import App, device_db
from core import helpers
from core.config import paths
from core.helpers import format_db_path

logger = logging.getLogger(__name__)


def register_blueprints(flaskapp):
    from server.blueprints import app as app
    from server.blueprints import workflowresult
    flaskapp.register_blueprint(app.app_page, url_prefix='/appinterface/<app>')
    flaskapp.register_blueprint(workflowresult.workflowresults_page, url_prefix='/workflowresults')
    __register_all_app_blueprints(flaskapp)


def __get_blueprints_in_module(module, sub_module_name='display'):
    from importlib import import_module
    from apps import AppBlueprint
    import_module('{0}.{1}'.format(module.__name__, sub_module_name))
    submodule = getattr(module, sub_module_name)
    blueprints = [getattr(submodule, field)
                  for field in dir(submodule) if (not field.startswith('__')
                                                  and isinstance(getattr(submodule, field), AppBlueprint))]
    return blueprints


def __register_app_blueprint(flaskapp, blueprint, url_prefix):
    rule = '{0}{1}'.format(url_prefix, blueprint.rule) if blueprint.rule else url_prefix
    flaskapp.register_blueprint(blueprint.blueprint, url_prefix=rule)


def __register_blueprint(flaskapp, blueprint, url_prefix):
    rule = '{0}{1}'.format(url_prefix, blueprint.rule) if blueprint.rule else url_prefix
    flaskapp.register_blueprint(blueprint.blueprint, url_prefix=rule)


def __register_app_blueprints(flaskapp, app_name, blueprints):
    url_prefix = '/apps/{0}'.format(app_name.split('.')[-1])
    for blueprint in blueprints:
        __register_blueprint(flaskapp, blueprint, url_prefix)


def __register_all_app_blueprints(flaskapp):
    from core.helpers import import_submodules
    import apps
    imported_apps = import_submodules(apps)
    for app_name, app_module in imported_apps.items():
        try:
            display_blueprints = __get_blueprints_in_module(app_module)
        except ImportError:
            pass
        else:
            __register_app_blueprints(flaskapp, app_name, display_blueprints)

        try:
            blueprints = __get_blueprints_in_module(app_module, sub_module_name='events')
        except ImportError:
            pass
        else:
            __register_app_blueprints(flaskapp, app_name, blueprints)


def create_app():
    import core.config
    connexion_app = connexion.App(__name__, specification_dir='api/')
    _app = connexion_app.app
    _app.jinja_loader = FileSystemLoader(['server/templates'])
    _app.config.update(
        # CHANGE SECRET KEY AND SECURITY PASSWORD SALT!!!
        SECRET_KEY=core.config.config.secret_key,
        SQLALCHEMY_DATABASE_URI=format_db_path(core.config.config.walkoff_db_type, os.path.abspath(paths.db_path)),
        SECURITY_PASSWORD_HASH='pbkdf2_sha512',
        SECURITY_TRACKABLE=False,
        SECURITY_PASSWORD_SALT='something_super_secret_change_in_production',
        SECURITY_POST_LOGIN_VIEW='/',
        WTF_CSRF_ENABLED=False,
        JWT_BLACKLIST_ENABLED=True,
        JWT_BLACKLIST_TOKEN_CHECKS=['refresh'],
        JWT_TOKEN_LOCATION='headers',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    from server.database import db
    db.init_app(_app)
    from server.security import jwt
    jwt.init_app(_app)

    connexion_app.add_api('composed_api.yaml')
    register_blueprints(_app)
    core.config.config.initialize()

    import core.controller
    core.controller.controller.load_playbooks()
    return _app


# Template Loader
env = Environment(loader=FileSystemLoader("apps"))
app = create_app()


# Creates Test Data
@app.before_first_request
def create_user():
    from server.context import running_context
    from server.database import add_user, User, ResourcePermission, Role, initialize_resource_roles_from_database

    running_context.db.create_all()
    if not User.query.all():
        admin_role = running_context.Role(
            name='admin', description='administrator', resources=server.database.default_resources)
        running_context.db.session.add(admin_role)
        admin_user = add_user(username='admin', password='admin')
        admin_user.roles.append(admin_role)
        running_context.db.session.commit()
    if Role.query.all() or ResourcePermission.query.all():
        initialize_resource_roles_from_database()

    apps = set(helpers.list_apps()) - set([_app.name
                                           for _app in device_db.session.query(App).all()])
    app.logger.debug('Found apps: {0}'.format(apps))
    for app_name in apps:
        device_db.session.add(App(name=app_name, devices=[]))
    running_context.db.session.commit()
    device_db.session.commit()
    running_context.CaseSubscription.sync_to_subscriptions()

    app.logger.handlers = logging.getLogger('server').handlers
