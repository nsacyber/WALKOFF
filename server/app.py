import os
import logging
from jinja2 import Environment, FileSystemLoader

import server.database
from core import helpers
from core.config import paths
import core.config.config
import connexion
from core.helpers import format_db_path
from server.appdevice import App, device_db

logger = logging.getLogger(__name__)


def read_and_indent(filename, indent):
    indent = '  ' * indent
    with open(filename, 'r') as file_open:
        return ['{0}{1}'.format(indent, line) for line in file_open]


def compose_yamls():
    with open(os.path.join(paths.api_path, 'api.yaml'), 'r') as api_yaml:
        final_yaml = []
        for line_num, line in enumerate(api_yaml):
            if line.lstrip().startswith('$ref:'):
                split_line = line.split('$ref:')
                reference = split_line[1].strip()
                indentation = split_line[0].count('  ')
                try:
                    final_yaml.extend(read_and_indent(os.path.join(paths.api_path, reference), indentation))
                    final_yaml.append(os.linesep)
                except (IOError, OSError):
                    logger.error('Could not find or open referenced YAML file {0} in line {1}'.format(reference,
                                                                                                      line_num))
            else:
                final_yaml.append(line)
    with open(os.path.join(paths.api_path, 'composed_api.yaml'), 'w') as composed_yaml:
        composed_yaml.writelines(final_yaml)


def register_blueprints(flaskapp):
    from server.blueprints import app as app
    from server.blueprints import events, widgets, workflowresult
    flaskapp.register_blueprint(app.app_page, url_prefix='/appinterface/<app>')
    flaskapp.register_blueprint(widgets.widgets_page, url_prefix='/apps/<app>/widgets/<widget>')
    flaskapp.register_blueprint(events.events_page, url_prefix='/events')
    flaskapp.register_blueprint(workflowresult.workflowresults_page, url_prefix='/workflowresults')
    __register_all_app_blueprints(flaskapp)


def __get_blueprints_in_module(module, sub_module_name='display'):
    from importlib import import_module
    from apps import AppWidgetBlueprint
    import_module('{0}.{1}'.format(module.__name__, sub_module_name))
    submodule = getattr(module, sub_module_name)
    blueprints = [getattr(submodule, field)
                  for field in dir(submodule) if (not field.startswith('__')
                                                  and isinstance(getattr(submodule, field), AppWidgetBlueprint))]
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

        __register_all_app_widget_blueprints(flaskapp, app_module)


def __register_all_app_widget_blueprints(flaskapp, app_module):
    from importlib import import_module
    from core.helpers import import_submodules
    try:
        widgets_module = import_module('{0}.widgets'.format(app_module.__name__))
    except ImportError:
        return
    else:
        app_name = app_module.__name__.split('.')[-1]
        imported_widgets = import_submodules(widgets_module)
        for widget_name, widget_module in imported_widgets.items():
            try:
                blueprints = __get_blueprints_in_module(widget_module)
            except ImportError:
                continue
            else:
                url_prefix = '/apps/{0}/{1}'.format(app_name, widget_name.split('.')[-1])
                for blueprint in blueprints:
                    __register_blueprint(flaskapp, blueprint, url_prefix)


def create_app():
    from .blueprints.events import setup_case_stream
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
        STATIC_FOLDER=os.path.abspath('server/static'),
        JWT_BLACKLIST_ENABLED=True,
        JWT_BLACKLIST_TOKEN_CHECKS=['refresh']
    )
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    _app.config['JWT_TOKEN_LOCATION'] = 'headers'

    from server.database import db
    db.init_app(_app)
    from server.security import jwt
    jwt.init_app(_app)

    connexion_app.add_api('composed_api.yaml')
    register_blueprints(_app)
    core.config.config.initialize()

    import core.controller
    core.controller.controller.load_playbooks()
    setup_case_stream()
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
        admin_role = running_context.Role(name='admin', description='administrator', resources=server.database.default_resources)
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


def create_test_data():
    from server.context import running_context
    from . import database

    running_context.db.create_all()

    if not database.User.query.first():
        admin_role = running_context.user_datastore.create_role(name='admin',
                                                                description='administrator',
                                                                pages=server.database.default_resources)

        u = running_context.User.add_user(username='admin', password='admin')
        running_context.user_datastore.add_role_to_user(u, admin_role)
        running_context.db.session.commit()

    apps = set(helpers.list_apps()) - set([_app.name
                                           for _app in device_db.session.query(App).all()])
    app.logger.debug('Found apps: {0}'.format(apps))
    for app_name in apps:
        device_db.session.add(App(app=app_name, devices=[]))
    running_context.db.session.commit()
    device_db.session.commit()
    running_context.CaseSubscription.sync_to_subscriptions()

    app.logger.handlers = logging.getLogger('server').handlers
