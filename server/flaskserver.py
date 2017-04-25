import json
import os
import sys

from flask import render_template
from flask_security import login_required, auth_token_required, current_user, roles_accepted
from flask_security.utils import encrypt_password
from gevent import monkey
import xml.dom.minidom as minidom
from xml.etree import ElementTree
import core.config.config
import core.config.paths
import core.filters
import core.flags
from core import helpers

from core.helpers import combine_dicts
from server.context import running_context
from . import database, interface
from server import app

monkey.patch_all()

urls = ['/', '/key', '/playbook', '/configuration', '/interface', '/execution/listener',
        '/execution/listener/triggers',
        '/roles', '/users', '/configuration', '/cases', '/apps', '/execution/scheduler']

default_urls = urls
database.initialize_user_roles(urls)


# Creates Test Data
@app.before_first_request
def create_user():
    running_context.db.create_all()

    if not database.User.query.first():
        admin_role = running_context.user_datastore.create_role(name='admin',
                                                                description='administrator',
                                                                pages=default_urls)

        u = running_context.user_datastore.create_user(email='admin', password=encrypt_password('admin'))

        running_context.user_datastore.add_role_to_user(u, admin_role)

        running_context.db.session.commit()

    apps = set(helpers.list_apps()) - set([_app.name
                                           for _app in running_context.db.session.query(running_context.App).all()])
    for app_name in apps:
        running_context.db.session.add(running_context.App(app=app_name, devices=[]))
    running_context.db.session.commit()

    running_context.CaseSubscription.sync_to_subscriptions()

"""
    URLS
"""


@app.route('/')
@login_required
def default():
    if current_user.is_authenticated:
        default_page_name = 'dashboard'
        args = {"apps": running_context.get_apps(),
                "authKey": current_user.get_auth_token(),
                "currentUser": current_user.email,
                "default_page": default_page_name}
        return render_template("container.html", **args)
    else:
        return {"status": "Could Not Log In."}


# Returns System-Level Interface Pages
@app.route('/interface/<string:name>/display', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/interface'])
def system_pages(name):
    if current_user.is_authenticated and name:
        args = getattr(interface, name)()
        combine_dicts(args, {"authKey": current_user.get_auth_token()})
        return render_template("pages/" + name + "/index.html", **args)
    else:
        return {"status": "Could Not Log In."}


# Returns the API key for the user
@app.route('/key', methods=['GET', 'POST'])
@login_required
def login_info():
    if current_user.is_authenticated:
        return json.dumps({"auth_token": current_user.get_auth_token()})
    else:
        return {"status": "Could Not Log In."}


@app.route('/apps/', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/apps'])
def list_all_apps():
    return json.dumps({"apps": helpers.list_apps()})


@app.route('/apps/actions', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/apps'])
def list_all_apps_and_actions():
    core.config.config.load_function_info()
    return json.dumps(core.config.config.function_info['apps'])


def write_playbook_to_file(playbook_name):
    write_format = 'w' if sys.version_info[0] == 2 else 'wb'
    playbook_filename = os.path.join(core.config.paths.workflows_path, '{0}.workflow'.format(playbook_name))
    with open(playbook_filename, write_format) as workflow_out:
        xml = ElementTree.tostring(running_context.controller.playbook_to_xml(playbook_name))
        xml_dom = minidom.parseString(xml).toprettyxml(indent='\t')
        workflow_out.write(xml_dom.encode('utf-8'))


@app.route('/flags', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def display_flags():
    core.config.config.load_function_info()
    return json.dumps({"status": "success", "flags": core.config.config.function_info['flags']})


@app.route('/filters', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def display_filters():
    return json.dumps({"status": "success", "filters": core.config.config.function_info['filters']})
