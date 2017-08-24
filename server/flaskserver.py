import json
import os
import logging
import sys
from flask import render_template, send_from_directory, request, jsonify, redirect, url_for, Response, make_response
from server.security import current_user, roles_accepted, verify_password, create_access_token, auth_token_required, create_refresh_token
from flask_jwt_extended import set_access_cookies, set_refresh_cookies, unset_jwt_cookies, get_jwt_identity, current_user
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

logger = logging.getLogger(__name__)

monkey.patch_all()

urls = ['/', '/key', '/playbooks', '/configuration', '/interface', '/execution/listener',
        '/execution/listener/triggers', '/metrics',
        '/roles', '/users', '/configuration', '/cases', '/apps', '/execution/scheduler']

default_urls = urls
database.initialize_user_roles(urls)

@app.route('/')
@app.route('/controller')
@app.route('/playbook')
@app.route('/devices')
@app.route('/triggers')
@app.route('/cases')
@app.route('/settings')
def default():
    # args = {"apps": running_context.get_apps(),
    #         "authKey": current_user.get_auth_token(),
    #         "authKey": "",
    #         "currentUser": current_user.id,
    #         "default_page": 'controller'}
    args = {}
    return render_template("index.html", **args)

@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/availablesubscriptions', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def display_possible_subscriptions():
    return json.dumps(core.config.config.possible_events)


# Returns System-Level Interface Pages
@app.route('/interface/<string:name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/interface'])
def sys_pages(name):
    if current_user.is_authenticated and name:
        args = getattr(interface, name)()
        combine_dicts(args, {"authKey": current_user.get_auth_token()})
        return render_template("pages/" + name + "/index.html", **args)
    else:
        app.logger.debug('Unsuccessful login attempt')
        return {"status": "Could Not Log In."}


# TODO: DELETE
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
@app.route('/key', methods=['POST'])
@auth_token_required
def login_info():
    print(get_jwt_identity())
    #user = database.User.query.filter(database.User.email == username).first()
    #if user:
    #     pass
    # else:
    #     app.logger.debug('Unsuccessful login attempt')
    #     return {"status": "Could Not Log In."}
    return "", 200

# Returns the API key for the user
@app.route('/login-process', methods=['POST'])
def login():
    print(request.data)
    data = request.get_json()
    print(data)
    username = data["username"]
    password = data["password"]
    user = database.User.query.filter(database.User.email == username).first()
    if user:
        if verify_password(user.password, password):
            access_token = create_access_token(identity=user)
            refresh_token = create_refresh_token(identity=user)
            #resp = jsonify({'login': True})
            # resp = Response(response=dict(login = True), status=200)
            # set_access_cookies(resp, access_token)
            # set_refresh_cookies(resp, refresh_token)

            # resp = Response(response=access_token, headers={"Authentication-Token": access_token}, status=200, is_redirect=True, url=url_for("/"))
            # resp = app.make_response(redirect(request.url_root, code=301))
            # resp.headers["Authentication-Token"] =  access_token
            return jsonify({'login': True, 'authentication-token': access_token})
        else:
            app.logger.debug('Unsuccessful login attempt')
            return jsonify({"login" : False})
    else:
        app.logger.debug('Unsuccessful login attempt')
        return jsonify({"login" : False})

@app.route('/logout', methods=['GET'])
def logout():
    return render_template("logout.html")

@app.route('/widgets', methods=['GET'])
@auth_token_required
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

# This is required by zone.js as it need to access the
# "main.js" file in the "ClientApp\app" folder which it
# does by accessing "<your-site-path>/app/main.js"
# @app.route('/app/<path:filename>')
# def client_app_app_folder(filename):
#     return send_from_directory(os.path.join(core.config.paths.client_path, "app"), filename)

# Creates Test Data
@app.before_first_request
def create_user():
    from server.context import running_context
    from . import database
    from server import flaskserver
    from server.security import encrypt_password

    database.db.create_all()

    if not database.User.query.first():
        admin_role = database.Role.create_role(name='admin',
                                               description='administrator',
                                               pages=flaskserver.default_urls)

        u = database.User.create_user(email='admin', password=encrypt_password('admin'))
        database.Role.add_role_to_user(u, admin_role)
        database.db.session.commit()

    apps = set(helpers.list_apps()) - set([_app.name
                                           for _app in database.db.session.query(running_context.App).all()])
    app.logger.debug('Found apps: {0}'.format(apps))
    for app_name in apps:
        database.db.session.add(running_context.App(app=app_name, devices=[]))
    database.db.session.commit()

    running_context.CaseSubscription.sync_to_subscriptions()

    app.logger.handlers = logging.getLogger('server').handlers

# Custom static data
@app.route('/client/<path:filename>')
def client_app_folder(filename):
    return send_from_directory(os.path.abspath(core.config.paths.client_path), filename)