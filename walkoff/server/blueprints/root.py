import logging
import os

from flask import current_app
from flask import render_template, send_from_directory, Blueprint
from sqlalchemy.exc import SQLAlchemyError

import walkoff.config
from walkoff import helpers
from walkoff.executiondb.device import App
from walkoff.extensions import db
from walkoff.server.problem import Problem
from walkoff.server.returncodes import SERVER_ERROR

logger = logging.getLogger(__name__)

root_page = Blueprint('root_page', __name__)


# Custom static data
@root_page.route('client/<path:filename>')
def client_app_folder(filename):
    return send_from_directory(os.path.abspath(walkoff.config.Config.CLIENT_PATH), filename)


@root_page.route('/')
@root_page.route('playbook')
@root_page.route('execution')
@root_page.route('scheduler')
@root_page.route('devices')
@root_page.route('messages')
@root_page.route('cases')
@root_page.route('metrics')
@root_page.route('settings')
def default():
    return render_template("index.html")


@root_page.route('interfaces/<interface_name>')
def app_page(interface_name):
    return render_template("index.html")


@root_page.route('login')
def login_page():
    return render_template("login.html")


@root_page.errorhandler(SQLAlchemyError)
def handle_database_errors(e):
    current_app.logger.exception('Caught an unhandled SqlAlchemy exception.')
    return Problem(SERVER_ERROR, 'A database error occurred.', e.__class__.__name__)


@root_page.errorhandler(500)
def handle_generic_server_error(e):
    current_app.logger.exception('Caught an unhandled error.')
    return Problem(SERVER_ERROR, 'An error occurred in the server.', e.__class__.__name__)


@root_page.before_app_first_request
def create_user():
    from walkoff.serverdb import add_user, User, Role, initialize_default_resources_admin, \
        initialize_default_resources_guest
    db.create_all()

    # Setup admin and guest roles
    initialize_default_resources_admin()
    initialize_default_resources_guest()

    # Setup admin user
    admin_role = Role.query.filter_by(id=1).first()
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        add_user(username='admin', password='admin', roles=[1])
    elif admin_role not in admin_user.roles:
        admin_user.roles.append(admin_role)

    db.session.commit()

    apps = set(helpers.list_apps(walkoff.config.Config.APPS_PATH)) - set([_app.name
                                           for _app in
                                           current_app.running_context.execution_db.session.query(App).all()])
    current_app.logger.debug('Found new apps: {0}'.format(apps))
    for app_name in apps:
        current_app.running_context.execution_db.session.add(App(name=app_name, devices=[]))
    db.session.commit()
    current_app.running_context.execution_db.session.commit()
    send_all_cases_to_workers()
    current_app.logger.handlers = logging.getLogger('server').handlers


def send_all_cases_to_workers():
    from walkoff.serverdb.casesubscription import CaseSubscription
    from walkoff.case.database import Case
    from walkoff.case.subscription import Subscription
    current_app.logger.info('Sending existing cases to workers')
    for case_subscription in CaseSubscription.query.all():
        subscriptions = [Subscription(sub['id'], sub['events']) for sub in case_subscription.subscriptions]
        case = current_app.running_context.case_db.session.query(Case).filter(
            Case.name == case_subscription.name).first()
        if case is not None:
            current_app.running_context.executor.update_case(case.id, subscriptions)
