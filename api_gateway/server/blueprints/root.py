import logging
import os
from http import HTTPStatus

# from alembic.config import Config
# from alembic.runtime.migration import MigrationContext
# from alembic.script import ScriptDirectory
from flask import current_app
from flask import render_template, send_from_directory, Blueprint
from sqlalchemy.exc import SQLAlchemyError

from common.config import static
from common.config import config
from api_gateway.extensions import db
from api_gateway.server.problem import Problem

logger = logging.getLogger(__name__)

root_page = Blueprint('root_page', __name__, template_folder="api_gateway/client/")


# Custom static data
@root_page.route('/walkoff/client/<path:filename>')
def client_app_folder(filename):
    return send_from_directory(os.path.abspath(static.CLIENT_PATH), filename)


# Default route to angular application
@root_page.route('/', defaults={'path': ''})
@root_page.route('/walkoff/', defaults={'path': ''})
@root_page.route('/walkoff/<path:path>')
def default(path):
    return send_from_directory(os.path.abspath(static.CLIENT_PATH), "dist/walkoff/index.html")


# Route to login page
@root_page.route('/walkoff/login')
def login_page():
    return render_template("login.html")


@root_page.errorhandler(SQLAlchemyError)
def handle_database_errors(e):
    current_app.logger.exception('Caught an unhandled SqlAlchemy exception.')
    return Problem(HTTPStatus.INTERNAL_SERVER_ERROR, 'A database error occurred.', e.__class__.__name__)


@root_page.errorhandler(500)
def handle_generic_server_error(e):
    current_app.logger.exception('Caught an unhandled error.')
    return Problem(HTTPStatus.INTERNAL_SERVER_ERROR, 'An error occurred in the server.', e.__class__.__name__)


@root_page.before_app_first_request
def create_user():
    from api_gateway.serverdb import add_user, User, Role, initialize_default_resources_admin, \
        initialize_default_resources_internal_user, \
        initialize_default_resources_workflow_developer, \
        initialize_default_resources_app_developer, \
        initialize_default_resources_workflow_operator, initialize_default_resources_super_admin
    from sqlalchemy_utils import database_exists, create_database

    if not database_exists(db.engine.url):
        create_database(db.engine.url)
    db.create_all()

    # alembic_cfg = Config(api_gateway.config.Config.ALEMBIC_CONFIG, ini_section="walkoff",
    #                      attributes={'configure_logger': False})
    #
    # # This is necessary for a flask database
    # connection = db.engine.connect()
    # context = MigrationContext.configure(connection)
    # script = ScriptDirectory.from_config(alembic_cfg)
    # context.stamp(script, "head")

    # Setup internal, super_admin, admin workflow_developer, and workflow_operator roles
    initialize_default_resources_internal_user()
    initialize_default_resources_super_admin()
    initialize_default_resources_admin()
    initialize_default_resources_app_developer()
    initialize_default_resources_workflow_developer()
    initialize_default_resources_workflow_operator()

    # Setup internal user
    internal_role = Role.query.filter_by(id=1).first()
    internal_user = User.query.filter_by(username="internal_user").first()
    if not internal_user:
        key = config.get_from_file(config.INTERNAL_KEY_PATH)
        add_user(username='internal_user', password=key, roles=[2])
    elif internal_role not in internal_user.roles:
        internal_user.roles.append(internal_role)

    # Setup Super Admin user
    super_admin_role = Role.query.filter_by(id=2).first()
    super_admin_user = User.query.filter_by(username="super_admin").first()
    if not super_admin_user:
        add_user(username='super_admin', password='super_admin', roles=[2])
    elif super_admin_role not in super_admin_user.roles:
        super_admin_user.roles.append(super_admin_role)

    # Setup Admin user
    admin_role = Role.query.filter_by(id=3).first()
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        add_user(username='admin', password='admin', roles=[3])
    elif admin_role not in admin_user.roles:
        admin_user.roles.append(admin_role)

    db.session.commit()

    # apps = set(helpers.list_apps(api_gateway.config.Config.APPS_PATH)) - set([_app.name
    #                                                                       for _app in
    #                                                                       current_app.running_context.execution_db.session.query(
    #                                                                           App).all()])
    # current_app.logger.debug('Found new apps: {0}'.format(apps))
    # for app_name in apps:
    #     current_app.running_context.execution_db.session.add(App(name=app_name, devices=[]))
    # db.session.commit()
    # current_app.running_context.execution_db.session.commit()
    # reschedule_all_workflows()
    # current_app.logger.handlers = logging.getLogger('server').handlers


def reschedule_all_workflows():
    from api_gateway.serverdb.scheduledtasks import ScheduledTask
    current_app.logger.info('Scheduling workflows')
    for task in (task for task in ScheduledTask.query.all() if task.status == 'running'):
        current_app.logger.debug(f"Rescheduling task {task.name} (id={task.id})")
        task._start_workflows()
