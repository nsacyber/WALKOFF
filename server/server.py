import database
import app
import os
import ssl
import json

from flask import render_template
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
from flask_security import auth_token_required, current_user, roles_required

from core import config, interface
from flask_security.utils import encrypt_password, verify_and_update_password
from core import forms
from jinja2 import Environment, FileSystemLoader
from core.ffk import Flag
from core.workflow import Workflow

app = app.app
env = app.env

db = database.db


class Triggers(Base):
    __tablename__ = "triggers"
    name = db.Column(db.String(255), nullable=False)
    play = db.Column(db.String(255), nullable=False)
    condition = db.Column(db.String(255, convert_unicode=False), nullable=False)

    def __init__(self, name, play, condition):
        self.name = name
        self.play = play
        self.condition = condition

    def edit_trigger(self, form=None):
        if form:
            if form.name.data:
                self.name = form.name.data

            if form.play.data:
                self.play = form.play.data

            if form.conditional.data:
                self.condition = str(form.conditional.data)

        return True

    def as_json(self):
        return {'name': self.name,
                'conditions': self.condition,
                'play': self.play}

    @staticmethod
    def execute(data_in):
        triggers = Triggers.query.all()
        listener_output = {}
        for trigger in triggers:
            conditionals = json.loads(trigger.condition)
            if all(Triggers.__execute_trigger(conditional, data_in) for conditional in conditionals):
                workflow_to_be_executed = Workflow.get_workflow(trigger.play)
                if workflow_to_be_executed:
                    trigger_results = workflow_to_be_executed.execute()
                else:
                    return json.dumps({"status": "trigger error: play could not be found"})
                listener_output[trigger.name] = json.loads(str(trigger_results[0]))
        return listener_output

    @staticmethod
    def __execute_trigger(conditional, data_in):
        conditional = json.loads(conditional)
        return Flag(**conditional)(data_in)

    def __repr__(self):
        return json.dumps(self.as_json())

    def __str__(self):
        out = {'name': self.name,
               'conditions': json.loads(self.condition),
               'play': self.play}
        return json.dumps(out)

""""
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


@app.route("/workflow/", methods=['GET'])
def workflow():
    return ""


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


@app.route('/execution/listener/triggers/<string:action>', methods=["POST"])
@auth_token_required
@roles_required("admin")
def triggerManagement(action):
    if action == "add":
        form = forms.addNewTriggerForm(request.form)
        if form.validate():
            query = Triggers.query.filter_by(name=form.name.data).first()
            if query is None:
                db.session.add(
                    Triggers(name=form.name.data, condition=json.dumps(form.conditional.data), play=form.play.data))
                db.session.commit()

                return json.dumps({"status": "trigger successfully added"})
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
            db.session.commit()
            return json.dumps({"status": "removed trigger"})
        return json.dumps({"status": "could not remove trigger"})

    elif action == "display":
        query = Triggers.query.filter_by(name=name).first()
        if query:
            return str(query)
        return json.dumps({"status": "could not display trigger"})


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
