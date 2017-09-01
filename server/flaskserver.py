import json
import os
import logging
from flask import render_template, send_from_directory
from server.security import roles_accepted
from flask_jwt_extended import current_user, jwt_required, jwt_refresh_token_required, get_raw_jwt
import core.config.config
import core.config.paths
import core.filters
import core.flags
from core import helpers

from core.helpers import combine_dicts
from server.context import running_context
from . import database, interface
from server import app

logger = logging.getLogger(__name__)

urls = ['/', '/key', '/playbooks', '/configuration', '/interface', '/execution/listener',
        '/execution/listener/triggers', '/metrics',
        '/roles', '/users', '/configuration', '/cases', '/apps', '/execution/scheduler']

default_urls = urls
database.initialize_user_roles(urls)

# Custom static data
@app.route('/client/<path:filename>')
def client_app_folder(filename):
    return send_from_directory(os.path.abspath(core.config.paths.client_path), filename)

@app.route('/')
@app.route('/playbook')
@app.route('/scheduler')
@app.route('/devices')
@app.route('/triggers')
@app.route('/cases')
@app.route('/settings')
def default():
    return render_template("index.html")


@app.route('/login')
def login_page():
    return render_template("login.html")


@app.route('/availablesubscriptions', methods=['GET'])
@jwt_required
@roles_accepted(*running_context.user_roles['/cases'])
def display_possible_subscriptions():
    return json.dumps(core.config.config.possible_events)


# Returns System-Level Interface Pages
@app.route('/interface/<string:name>', methods=['GET'])
@jwt_required
@roles_accepted(*running_context.user_roles['/interface'])
def sys_pages(name):
    args = getattr(interface, name)()
    combine_dicts(args, {"authKey": current_user.get_auth_token()})
    return render_template("pages/" + name + "/index.html", **args)


# TODO: DELETE
@app.route('/interface/<string:name>/display', methods=['POST'])
@jwt_required
@roles_accepted(*running_context.user_roles['/interface'])
def system_pages(name):
    args = getattr(interface, name)()
    combine_dicts(args, {"authKey": current_user.get_auth_token()})
    return render_template("pages/" + name + "/index.html", **args)


@app.route('/logout', methods=['GET'])
@jwt_refresh_token_required
def logout():
    from server.tokens import revoke_token
    revoke_token(get_raw_jwt())
    return render_template("logout.html")



@app.route('/widgets', methods=['GET'])
@jwt_required
@roles_accepted(*running_context.user_roles['/apps'])
def list_all_widgets():
    return json.dumps({_app: helpers.list_widgets(_app) for _app in helpers.list_apps()})


def write_playbook_to_file(playbook_name):
    playbook_filename = os.path.join(core.config.paths.workflows_path, '{0}.playbook'.format(playbook_name))
    backup = None
    try:
        with open(playbook_filename) as original_file:
            backup = original_file.read()
        os.remove(playbook_filename)
    except (IOError, OSError):
        pass

    app.logger.debug('Writing playbook {0} to file'.format(playbook_name))
    write_format = 'w'

    try:
        with open(playbook_filename, write_format) as workflow_out:
            playbook_json = running_context.controller.playbook_as_json(playbook_name)
            workflow_out.write(json.dumps(playbook_json, sort_keys=True, indent=4, separators=(',', ': ')))
    except Exception as e:
        logger.error('Could not save playbook to file. Reverting file to original. '
                     'Error: {0}'.format(helpers.format_exception_message(e)))
        with open(playbook_filename, 'w') as f:
            f.write(backup)


