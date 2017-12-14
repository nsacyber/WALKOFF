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
from server.extensions import db, jwt
from server.database.casesubscription import CaseSubscription
from server.database import add_user, User, Role

logger = logging.getLogger(__name__)


def register_blueprints(flaskapp):
    from server.blueprints import custominterface
    from server.blueprints import workflowresult

    flaskapp.register_blueprint(custominterface.custom_interface_page, url_prefix='/custominterfaces/<interface>')
    flaskapp.register_blueprint(workflowresult.workflowresults_page, url_prefix='/workflowresults')
    __register_all_app_blueprints(flaskapp)


def __get_blueprints_in_module(module):
    from interfaces import AppBlueprint
    blueprints = [getattr(module, field)
                  for field in dir(module) if (not field.startswith('__')
                                               and isinstance(getattr(module, field), AppBlueprint))]
    return blueprints


def __register_app_blueprint(flaskapp, blueprint, url_prefix):
    rule = '{0}{1}'.format(url_prefix, blueprint.rule) if blueprint.rule else url_prefix
    flaskapp.register_blueprint(blueprint.blueprint, url_prefix=rule)


def __register_blueprint(flaskapp, blueprint, url_prefix):
    rule = '{0}{1}'.format(url_prefix, blueprint.rule) if blueprint.rule else url_prefix
    flaskapp.register_blueprint(blueprint.blueprint, url_prefix=rule)


def __register_app_blueprints(flaskapp, app_name, blueprints):
    url_prefix = '/interfaces/{0}'.format(app_name.split('.')[-1])
    for blueprint in blueprints:
        __register_blueprint(flaskapp, blueprint, url_prefix)


def __register_all_app_blueprints(flaskapp):
    from core.helpers import import_submodules
    import interfaces
    imported_apps = import_submodules(interfaces)
    for interface_name, interfaces_module in imported_apps.items():
        try:
            display_blueprints = []
            for submodule in import_submodules(interfaces_module, recursive=True).values():
                display_blueprints.extend(__get_blueprints_in_module(submodule))
        except ImportError:
            pass
        else:
            __register_app_blueprints(flaskapp, interface_name, display_blueprints)


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

    db.init_app(_app)
    jwt.init_app(_app)

    connexion_app.add_api('composed_api.yaml')

    core.config.config.initialize()
    register_blueprints(_app)

    import core.controller
    core.controller.controller.load_playbooks()
    return _app


# Template Loader
env = Environment(loader=FileSystemLoader("interfaces"))
app = create_app()


@app.before_first_request
def create_user():
    db.create_all()

    # Setup admin role
    admin_role = Role.query.filter_by(name="admin").first()
    if admin_role:
        admin_role.set_resources(server.database.default_resource_permissions)
    else:
        admin_role = Role(
            name='admin', description='administrator', resources=server.database.default_resource_permissions)
        db.session.add(admin_role)

    # Setup admin user
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        add_user(username='admin', password='admin', roles=["admin"])
    elif admin_role not in admin_user.roles:
        admin_user.roles.append(admin_role)

    db.session.commit()

    apps = set(helpers.list_apps()) - set([_app.name
                                           for _app in device_db.session.query(App).all()])
    app.logger.debug('Found apps: {0}'.format(apps))
    for app_name in apps:
        device_db.session.add(App(name=app_name, devices=[]))
    db.session.commit()
    device_db.session.commit()
    CaseSubscription.sync_to_subscriptions()

    app.logger.handlers = logging.getLogger('server').handlers
