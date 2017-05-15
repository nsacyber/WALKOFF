import os
import logging

from jinja2 import Environment, FileSystemLoader
from core import helpers
from core.config import paths
import core.config.config
import connexion
from gevent import monkey
from flask_security.utils import encrypt_password
from core.helpers import format_db_path

monkey.patch_all()

logger = logging.getLogger(__name__)


def read_and_indent(filename, indent):
    indent = '  ' * indent
    with open(filename, 'r') as file_open:
        return ['{0}{1}'.format(indent, line) for line in file_open]


def compose_yamls():
    with open(os.path.join(paths.swagger_apis, 'api.yaml'), 'r') as api_yaml:
        final_yaml = []
        for line_num, line in enumerate(api_yaml):
            if line.lstrip().startswith('$ref:'):
                split_line = line.split('$ref:')
                reference = split_line[1].strip()
                indentation = split_line[0].count('  ')
                try:
                    final_yaml.extend(read_and_indent(os.path.join(paths.swagger_apis, reference), indentation))
                    final_yaml.append('\n')
                except (IOError, OSError):
                    logger.error('Could not find or open referenced YAML file {0} in line {1}'.format(reference,
                                                                                                      line_num))
            else:
                final_yaml.append(line)
    with open(os.path.join(paths.swagger_apis, 'composed_api.yaml'), 'w') as composed_yaml:
        composed_yaml.writelines(final_yaml)


def create_app():
    connexion_app = connexion.App(__name__, specification_dir='swagger/', server='gevent')
    _app = connexion_app.app
    compose_yamls()
    _app.jinja_loader = FileSystemLoader(['server/templates'])

    _app.config.update(
        # CHANGE SECRET KEY AND SECURITY PASSWORD SALT!!!
        SECRET_KEY="SHORTSTOPKEYTEST",
        SQLALCHEMY_DATABASE_URI=format_db_path(core.config.config.walkoff_db_type, os.path.abspath(paths.db_path)),
        SECURITY_PASSWORD_HASH='pbkdf2_sha512',
        SECURITY_TRACKABLE=False,
        SECURITY_PASSWORD_SALT='something_super_secret_change_in_production',
        SECURITY_POST_LOGIN_VIEW='/',
        WTF_CSRF_ENABLED=False,
        STATIC_FOLDER=os.path.abspath('server/static')
    )

    _app.config["SECURITY_LOGIN_USER_TEMPLATE"] = "login_user.html"
    _app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    connexion_app.add_api('composed_api.yaml')
    return _app


# Template Loader
env = Environment(loader=FileSystemLoader("apps"))
app = create_app()


# Creates Test Data
@app.before_first_request
def create_user():
    from server.context import running_context
    from . import database
    from server import flaskserver

    running_context.db.create_all()

    if not database.User.query.first():
        admin_role = running_context.user_datastore.create_role(name='admin',
                                                                description='administrator',
                                                                pages=flaskserver.default_urls)

        u = running_context.user_datastore.create_user(email='admin', password=encrypt_password('admin'))
        running_context.user_datastore.add_role_to_user(u, admin_role)
        running_context.db.session.commit()

    apps = set(helpers.list_apps()) - set([_app.name
                                           for _app in running_context.db.session.query(running_context.App).all()])
    app.logger.debug('Found apps: {0}'.format(apps))
    for app_name in apps:
        running_context.db.session.add(running_context.App(app=app_name, devices=[]))
    running_context.db.session.commit()

    running_context.CaseSubscription.sync_to_subscriptions()

    app.logger.handlers = logging.getLogger('server').handlers
