import os
import ssl
import json
from flask import render_template, request, Response
from flask_security import login_required, auth_token_required, current_user, roles_accepted
from flask_security.utils import encrypt_password, verify_and_update_password
from core import config, interface, controller
from core import forms
from core.case import callbacks
from core.case.subscription import Subscription, set_subscriptions, CaseSubscriptions

import core.case.database as case_database
from . import database
from .app import app
from .database import User
from .device import Device
from .triggers import Triggers

import gevent
from gevent import monkey
monkey.patch_all()

user_datastore = database.user_datastore

urls = ["/", "/key", "/workflow", "/configuration", "/interface", "/execution/listener", "/execution/listener/triggers",
        "/roles", "/users", "/configuration", '/cases']


default_urls = urls
userRoles = database.userRoles
database.initialize_userRoles(urls)
db = database.db


# Creates Test Data
@app.before_first_request
def create_user():
    # db.drop_all()
    database.db.create_all()
    if not database.User.query.first():
        # Add Credentials to Splunk app
        # db.session.add(Device(name="deviceOne", app="splunk", username="admin", password="hello", ip="192.168.0.1", port="5000"))

        adminRole = user_datastore.create_role(name="admin", description="administrator", pages=default_urls)
        # userRole = user_datastore.create_role(name="user", description="user")

        u = user_datastore.create_user(email='admin', password=encrypt_password('admin'))
        # u2 = user_datastore.create_user(email='user', password=encrypt_password('user'))

        user_datastore.add_role_to_user(u, adminRole)

        database.db.session.commit()


# Temporary create controller
workflowManager = controller.Controller()
workflowManager.loadWorkflowsFromFile(path="tests/testWorkflows/basicWorkflowTest.workflow")
workflowManager.loadWorkflowsFromFile(path="tests/testWorkflows/multiactionWorkflowTest.workflow")

subs = {'defaultController':
            Subscription(subscriptions=
                         {'multiactionWorkflow':
                              Subscription(events=["InstanceCreated", "StepExecutionSuccess",
                                                   "NextStepFound", "WorkflowShutdown"])})}
set_subscriptions({'testExecutionEvents': CaseSubscriptions(subscriptions=subs)})

"""
    URLS
"""


@app.route("/")
@login_required
def default():
    if current_user.is_authenticated:
        default_page_name = "dashboard"
        args = {"apps": config.getApps(), "authKey": current_user.get_auth_token(), "currentUser": current_user.email, "default_page":default_page_name}
        return render_template("container.html", **args)
    else:
        return {"status": "Could Not Log In."}


# Returns the API key for the user
@app.route('/key', methods=["GET", "POST"])
@login_required
def loginInfo():
    if current_user.is_authenticated:
        return json.dumps({"auth_token": current_user.get_auth_token()})
    else:
        return {"status": "Could Not Log In."}


@app.route("/workflow/<string:name>/<string:format>", methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles["/workflow"])
def workflow(name, format):
    if name in workflowManager.workflows:
        if format == "cytoscape":
            output = workflowManager.workflows[name].returnCytoscapeData()
            return json.dumps(output)
        if format == "execute":
            history = callbacks.cases["testExecutionEvents"]
            with history:
                steps, instances = workflowManager.executeWorkflow(name=name, start="start")

            responseFormat = request.form.get("format")
            if responseFormat == "cytoscape":
                # response = json.dumps(helpers.returnCytoscapeData(steps=steps))
                response = str(history.history)
            else:
                response = json.dumps(str(steps))
            callbacks.cases["testExecutionEvents"].clear_history()
            return response


@app.route('/cases', methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def display_cases():
    return json.dumps({'cases': [case.as_json(with_events=False)
                                 for case in case_database.case_db.session.query(case_database.Cases).all()]})


@app.route('/cases/<string:case_name>', methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def display_case(case_name):
    case = case_database.case_db.session.query(case_database.Cases)\
        .filter(case_database.Cases.name == case_name).first()
    if case:
        return json.dumps({'case': case.as_json()})
    else:
        return json.dumps({'status': 'Case with given name does not exist'})

@app.route("/configuration/<string:key>", methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def configValues(key):
    if current_user.is_authenticated and key:
        if hasattr(config, key):
            return json.dumps({str(key): str(getattr(config, key))})


# Returns System-Level Interface Pages
@app.route('/interface/<string:name>/display', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/interface"])
def systemPages(name):
    if current_user.is_authenticated and name:
        args, form = getattr(interface, name)()
        return render_template("pages/" + name + "/index.html", form=form, **args)
    else:
        return {"status": "Could Not Log In."}


# Controls execution triggers
@app.route('/execution/listener', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/execution/listener"])
def listener():
    form = forms.incomingDataForm(request.form)
    listener_output = Triggers.execute(form.data.data) if form.validate() else {}
    return json.dumps(listener_output)


@app.route('/execution/listener/triggers', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/execution/listener/triggers"])
def displayAllTriggers():
    result = str(Triggers.query.all())
    return result


@app.route('/execution/listener/triggers/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/execution/listener/triggers"])
def triggerManagement(action):
    if action == "add":
        form = forms.addNewTriggerForm(request.form)
        if form.validate():
            query = Triggers.query.filter_by(name=form.name.data).first()
            if query is None:
                database.db.session.add(
                    Triggers(name=form.name.data, condition=json.dumps(form.conditional.data), play=form.play.data))

                database.db.session.commit()
                return json.dumps({"status": "trigger successfully added"})
            else:
                return json.dumps({"status": "trigger with that name already exists"})
        return json.dumps({"status": "trigger could not be added"})


@app.route('/execution/listener/triggers/<string:name>/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/execution/listener/triggers"])
def triggerFunctions(action, name):
    if action == "edit":
        form = forms.editTriggerForm(request.form)
        trigger = Triggers.query.filter_by(name=name).first()
        if form.validate() and trigger is not None:
            # Ensures new name is unique
            if form.name.data:
                if len(Triggers.query.filter_by(name=form.name.data).all()) > 0:
                    return json.dumps({"status": "device could not be edited"})

            result = trigger.editTrigger(form)

            if result:
                db.session.commit()
                return json.dumps({"status": "device successfully edited"})

        return json.dumps({"status": "device could not be edited"})

    elif action == "remove":
        query = Triggers.query.filter_by(name=name).first()
        if query:
            Triggers.query.filter_by(name=name).delete()
            database.db.session.commit()
            return json.dumps({"status": "removed trigger"})
        elif query is None:
            json.dumps({"status": "trigger does not exist"})
        return json.dumps({"status": "could not remove trigger"})

    elif action == "display":
        query = Triggers.query.filter_by(name=name).first()
        if query:
            return str(query)
        return json.dumps({"status": "could not display trigger"})


# Controls roles
@app.route('/roles/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/roles"])
def roleAddActions(action):
    # Adds a new role
    if action == "add":
        form = forms.NewRoleForm(request.form)
        if form.validate():
            if not database.Role.query.filter_by(name=form.name.data).first():
                n = form.name.data

                if form.description.data is not None:
                    d = form.description.data
                    user_datastore.create_role(name=n, description=d, pages=default_urls)
                else:
                    user_datastore.create_role(name=n, pages=default_urls)

                database.add_to_userRoles(n, default_urls)

                db.session.commit()
                return json.dumps({"status": "role added " + n})
            else:
                return json.dumps({"status": "role exists"})
        else:
            return json.dumps({"status": "invalid input"})
    else:
        return json.dumps({"status": "invalid input"})


@app.route('/roles/<string:action>/<string:name>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/roles"])
def roleActions(action, name):
    role = database.Role.query.filter_by(name=name).first()

    if role:

        if action == "edit":
            form = forms.EditRoleForm(request.form)
            if form.validate():
                if form.description.data:
                    role.setDescription(form.description.data)
                if form.pages.data:
                    database.add_to_userRoles(name, form.pages)
            return json.dumps(role.display())

        elif action == "display":
            return json.dumps(role.display())
        else:
            return json.dumps({"status": "invalid input"})

    return json.dumps({"status": "role does not exist"})


# Controls non-specific users and roles
@app.route('/users/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/users"])
def userNonSpecificActions(action):
    # Adds a new user
    if action == "add":
        form = forms.NewUserForm(request.form)
        if form.validate():
            if not database.User.query.filter_by(email=form.username.data).first():
                un = form.username.data
                pw = encrypt_password(form.password.data)

                # Creates User
                u = user_datastore.create_user(email=un, password=pw)

                if form.role.entries:
                    u.setRoles(form.role.entries)

                db.session.commit()
                return json.dumps({"status": "user added " + str(u.id)})
            else:
                return json.dumps({"status": "user exists"})
        else:
            return json.dumps({"status": "invalid input"})


# Controls non-specific users and roles
@app.route('/users', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/users"])
def displayAllUsers():
    form = forms.UserForm(request.form)

    result = str(User.query.all())
    form.state.choices = result;
    return render_template('user.html', form=form)


# Controls non-specific users and roles
@app.route('/users/<string:id_or_email>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/users"])
def displayUser(id_or_email):
    user = user_datastore.get_user(id_or_email)
    if user:
        return json.dumps(user.display())
    else:
        return json.dumps({"status": "could not display user"})


# Controls users and roles
@app.route('/users/<string:id_or_email>/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/users"])
def userActions(action, id_or_email):
    user = user_datastore.get_user(id_or_email)
    if user:
        if action == "remove":
            if user != current_user:
                user_datastore.delete_user(user)
                db.session.commit()
                return json.dumps({"status": "user removed"})
            else:
                return json.dumps({"status": "user could not be removed"})

        elif action == "edit":
            form = forms.EditUserForm(request.form)
            if form.validate():
                if form.password:
                    verify_and_update_password(form.password.data, user)
                if form.role.entries:
                    user.setRoles(form.role.entries)

            return json.dumps(user.display())

        elif action == "display":
            if user is not None:
                return json.dumps(user.display())
            else:
                return json.dumps({"status": "could not display user"})



# Controls the non-specific app device configuration
@app.route('/configuration/<string:app>/devices/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def configDevicesConfig(app, action):
    if action == "add":
        form = forms.AddNewDeviceForm(request.form)
        if form.validate():
            if len(Device.query.filter_by(name=form.name.data).all()) > 0:
                return json.dumps({"status": "device could not be added"})
            db.session.add(
                Device(name=form.name.data, app=form.app.data, username=form.username.data, password=form.pw.data,
                       ip=form.ipaddr.data, port=form.port.data, other=form.other.data))
            db.session.commit()

            return json.dumps({"status": "device successfully added"})
        return json.dumps({"status": "device could not be added"})
    if action == "all":
        query = Device.query.with_entities(Device.name, Device.username, Device.port, Device.ip, Device.app).filter_by(
            app=app).all()
        output = []
        if query:
            for device in query:
                output.append(
                    {"name": device[0], "username": device[1], "port": device[2], "ip": device[3], "app": device[4]})

            return json.dumps(output)
    return json.dumps({"status": "could not display all devices"})


# Controls the specific app device configuration
@app.route('/configuration/<string:app>/devices/<string:device>/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def configDevicesConfigId(app, device, action):
    if action == "display":
        query = Device.query.with_entities(Device.name, Device.username, Device.port, Device.ip, Device.app).filter_by(
            app=app, name=device).first()
        if query:
            output = {"name": query[0], "username": query[1], "port": query[2], "ip": query[3], "app": query[4]}
            return json.dumps(output)
        return json.dumps({"status": "could not display device"})

    elif action == "remove":
        query = Device.query.filter_by(app=app, name=device).first()
        if query:
            Device.query.filter_by(app=app, name=device).delete()

            db.session.commit()
            return json.dumps({"status": "removed device"})
        return json.dumps({"status": "could not remove device"})

    elif action == "edit":
        form = forms.EditDeviceForm(request.form)
        device = Device.query.filter_by(app=app, name=device).first()
        if form.validate() and device is not None:
            # Ensures new name is unique
            if len(Device.query.filter_by(name=str(device)).all()) > 0:
                return json.dumps({"status": "device could not be edited"})

            device.editDevice(form)

            db.session.commit()
            return json.dumps({"status": "device successfully edited"})
        return json.dumps({"status": "device could not be edited"})



# Start Flask
def start(config_type=None):
    global db, env

    if config.https.lower() == "true":
        # Sets up HTTPS
        if config.TLS_version == "1.2":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        elif config.TLS_version == "1.1":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        # Provide user with informative error message
        displayIfFileNotFound(config.certificatePath)
        displayIfFileNotFound(config.privateKeyPath)

        context.load_cert_chain(config.certificatePath, config.privateKeyPath)
        app.run(debug=config.debug, ssl_context=context, host=config.host, port=int(config.port), threaded=True)
    else:
        app.run(debug=config.debug, host=config.host, port=int(config.port), threaded=True)


def displayIfFileNotFound(filepath):
    if not os.path.isfile(filepath):
        print("File not found: " + filepath)
