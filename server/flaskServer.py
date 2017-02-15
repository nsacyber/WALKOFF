from .app import app
from server import database
from .triggers import Triggers
import os
import ssl
import json
from flask import render_template, request
from flask_security import login_required, auth_token_required, current_user, roles_required
from flask_security.utils import encrypt_password, verify_and_update_password
from core import config, interface, controller
from core import forms

user_datastore = database.user_datastore

# Creates Test Data
@app.before_first_request
def create_user():
    # db.drop_all()
    database.db.create_all()
    if not database.User.query.first():
        # Add Credentials to Splunk app
        # db.session.add(Device(name="deviceOne", app="splunk", username="admin", password="hello", ip="192.168.0.1", port="5000"))

        adminRole = user_datastore.create_role(name="admin", description="administrator")
        # userRole = user_datastore.create_role(name="user", description="user")

        u = user_datastore.create_user(email='admin', password=encrypt_password('admin'))
        # u2 = user_datastore.create_user(email='user', password=encrypt_password('user'))

        user_datastore.add_role_to_user(u, adminRole)

        database.db.session.commit()

#Temporary create controller
workflowManager = controller.Controller()
workflowManager.loadWorkflowsFromFile(path="tests/testWorkflows/basicWorkflowTest.workflow")
workflowManager.loadWorkflowsFromFile(path="tests/testWorkflows/multiactionWorkflowTest.workflow")

"""
    URLS
"""


@app.route("/")
@login_required
def default():
    if current_user.is_authenticated:
        args = {"apps": config.getApps(), "authKey": current_user.get_auth_token(), "currentUser": current_user.email}
        return render_template("container.html", **args)
    else:
        return {"status": "Could Not Log In."}

#Returns the API key for the user
@app.route('/key', methods=["GET", "POST"])
@login_required
def loginInfo():
    if current_user.is_authenticated:
        return json.dumps({"auth_token" : current_user.get_auth_token()})
    else:
        return {"status" : "Could Not Log In."}

@app.route("/workflow/<string:name>/<string:format>", methods=['POST'])
@auth_token_required
@roles_required("admin")
def workflow(name, format):
    if name in workflowManager.workflows:
        if format == "cytoscape":
            output = workflowManager.workflows[name].returnCytoscapeData()
            return json.dumps(output)

@app.route("/configuration/<string:key>", methods=['POST'])
@auth_token_required
@roles_required("admin")
def configValues(key):
    if current_user.is_authenticated and key:
        if hasattr(config, key):
            return json.dumps({str(key): str(getattr(config, key))})


# Returns System-Level Interface Pages
@app.route('/interface/<string:name>/display', methods=["POST"])
@auth_token_required
@roles_required("admin")
def systemPages(name):
    if current_user.is_authenticated and name:
        args, form = getattr(interface, name)()
        return render_template("pages/" + name + "/index.html", form=form, **args)
    else:
        return {"status": "Could Not Log In."}


# Controls execution triggers
@app.route('/execution/listener', methods=["POST"])
@auth_token_required
@roles_required("admin")
def listener():
    form = forms.incomingDataForm(request.form)
    listener_output = Triggers.execute(form.data.data) if form.validate() else {}
    return json.dumps(listener_output)


@app.route('/execution/listener/triggers', methods=["POST"])
@auth_token_required
@roles_required("admin")
def displayAllTriggers():
    result = str(Triggers.query.all())
    return result


@app.route('/execution/listener/triggers/<string:action>', methods=["POST"])
@auth_token_required
@roles_required("admin")
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
@roles_required("admin")
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
        elif query == None:
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
@roles_required("admin")
def roleAddActions(action):
    # Adds a new role
    if action == "add":
        form = forms.NewRoleForm(request.form)
        if form.validate():
            if not database.Role.query.filter_by(name=form.name.data).first():
                n = form.name.data

                if form.description.data != None:
                    d = form.description.data
                    r = user_datastore.create_role(name=n, description=d)
                else:
                    r = user_datastore.create_role(name=n)

                db.session.commit()
                return json.dumps({"status" : "role added " + n})
            else:
                return json.dumps({"status" : "role exists"})
        else:
            return json.dumps({"status" : "invalid input"})

@app.route('/roles/<string:action>/<string:name>', methods=["POST"])
@auth_token_required
@roles_required("admin")
def roleActions(action, name):
    role = user_datastore.find_role(name=name)

    if role != None and role != []:

        if action == "edit":
            form = forms.EditRoleForm(request.form)
            if form.validate():
                if form.description != "":
                    role.setDescription(form.description.data)
            return json.dumps(role.display())

        elif action == "display":
            return json.dumps(role.display())
        else:
            return json.dumps({"status" : "invalid input"})

    return json.dumps({"status": "role does not exist"})

# Controls non-specific users and roles
@app.route('/users/<string:action>', methods=["POST"])
@auth_token_required
@roles_required("admin")
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

                if form.role.entries != [] and form.role.entries != None:
                    u.setRoles(form.role.entries)

                db.session.commit()
                return json.dumps({"status" : "user added " + str(u.id)})
            else:
                return json.dumps({"status" : "user exists"})
        else:
            return json.dumps({"status" : "invalid input"})

# Controls users and roles
@app.route('/users/<string:action>/<int:id>', methods=["POST"])
@auth_token_required
@roles_required("admin")
def userActions(action, id):
    user = user_datastore.get_user(id)
    if user != None and user != []:
        if action == "remove":
            if user != current_user:
                user_datastore.delete_user(user)
                db.session.commit()
                return json.dumps({"status" : "user removed"})
            else:
                return json.dumps({"status" : "user could not be removed"})

        elif action == "edit":
            form = forms.EditUserForm(request.form)
            if form.validate():
                if form.password != "":
                    verify_and_update_password(form.password.data, user)
                if form.role.entries != []:
                    user.setRoles(form.role.entries)

            return json.dumps(user.display())

        elif action == "display":
            if user != None:
                return json.dumps(user.display())
            else:
                return json.dumps({"status" : "could not display user"})


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
