import os
import ssl
import json
import sys
from flask import render_template, request
from flask_security import login_required, auth_token_required, current_user, roles_accepted
from flask_security.utils import encrypt_password, verify_and_update_password
import core.config.paths
import core.config.config
from core.context import running_context
from core.helpers import locate_workflows_in_directory
import core.flags
import core.filters
from core import helpers
from . import forms, interface
from core.case.subscription import CaseSubscriptions, add_cases, delete_cases, \
    rename_case
from core.options import Options
import core.case.database as case_database
import core.case.subscription as case_subscription
from . import database, appDevice
from .app import app
from .database import User
from .triggers import Triggers
from gevent import monkey
from server.appBlueprint import get_base_app_functions
from xml.etree import ElementTree
import pkgutil

monkey.patch_all()

user_datastore = database.user_datastore

urls = ["/", "/key", "/workflow", "/configuration", "/interface", "/execution/listener", "/execution/listener/triggers",
        "/roles", "/users", "/configuration", '/cases', '/apps']

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

    apps = set(helpers.list_apps()) - set([app.name for app in database.db.session.query(appDevice.App).all()])
    for app_name in apps:
        database.db.session.add(appDevice.App(app=app_name, devices=[]))
    database.db.session.commit()


"""
    URLS
"""


@app.route("/")
@login_required
def default():
    if current_user.is_authenticated:
        default_page_name = "dashboard"
        args = {"apps": running_context.getApps(), "authKey": current_user.get_auth_token(),
                "currentUser": current_user.email, "default_page": default_page_name}
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


@app.route('/apps/', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles["/apps"])
def list_all_apps():
    return json.dumps({"apps": helpers.list_apps()})


@app.route('/apps/actions', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles["/apps"])
def list_all_apps_and_actions():
    core.config.config.load_function_info()
    return json.dumps(core.config.config.function_info['apps'])


@app.route("/playbook", methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles["/workflow"])
def display_available_playbooks():
    try:
        workflows = {os.path.splitext(workflow)[0]:
                         helpers.get_workflow_names_from_file(os.path.join(core.config.paths.workflows_path, workflow))
                     for workflow in locate_workflows_in_directory(core.config.paths.workflows_path)}
        return json.dumps({"status": "success",
                           "playbooks": workflows})
    except Exception as e:
        return json.dumps({"status": "error: {0}".format(e)})


@app.route("/playbook/<string:name>", methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles["/workflow"])
def display_playbook_workflows(name):
    try:
        workflows = {os.path.splitext(workflow)[0]:
                         helpers.get_workflow_names_from_file(os.path.join(core.config.paths.workflows_path, workflow))
                     for workflow in locate_workflows_in_directory(core.config.paths.workflows_path)}

        if name in workflows:
            return json.dumps({"status": "success",
                               "workflows": workflows[name]})
        else:
            return json.dumps({"status": "error: name not found"})
    except Exception as e:
        return json.dumps({"status": "error: {0}".format(e)})


@app.route("/playbook/templates", methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles["/workflow"])
def display_available_workflow_templates():
    templates = {os.path.splitext(workflow)[0]:
                     helpers.get_workflow_names_from_file(os.path.join(core.config.paths.templates_path, workflow))
                 for workflow in locate_workflows_in_directory(core.config.paths.templates_path)}
    return json.dumps({"templates": templates})


@app.route("/playbook/<string:playbook_name>/<string:workflow_name>/display", methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles["/workflow"])
def display_workflow(playbook_name, workflow_name):
    if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
        return json.dumps({"status": "success",
                           "steps": running_context.controller.get_workflow(playbook_name,
                                                                            workflow_name).get_cytoscape_data(),
                           'options': running_context.controller.get_workflow(playbook_name,
                                                                              workflow_name).options.as_json()})
    else:
        return json.dumps({"status": "error: name not found"})


@app.route("/playbook/<string:playbook_name>/<string:action>", methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles["/workflow"])
def crud_playbook(playbook_name, action):
    if action == 'add':
        form = forms.AddPlaybookForm(request.form)
        if form.validate():
            status = 'success'
            template_playbook = form.playbook_template.data
            if template_playbook:
                if template_playbook in [os.path.splitext(workflow)[0]
                                         for workflow in
                                         locate_workflows_in_directory(core.config.paths.templates_path)]:
                    running_context.controller.create_playbook_from_template(playbook_name=playbook_name,
                                                                             template_playbook=template_playbook)
                else:
                    running_context.controller.create_playbook_from_template(playbook_name=playbook_name)
                    status = 'warning: template playbook not found. Using default template'
            else:
                running_context.controller.create_playbook_from_template(playbook_name=playbook_name)

            return json.dumps({"status": status,
                               "playbooks": running_context.controller.get_all_workflows()})

        else:
            return json.dumps({'status': 'error: invalid form'})
    elif action == 'edit':
        if running_context.controller.is_playbook_registerd(playbook_name):
            form = forms.EditPlaybookForm(request.form)
            if form.validate():
                new_name = form.new_name.data
                if new_name:
                    running_context.controller.update_playbook_name(playbook_name, new_name)
                    saved_playbooks = [os.path.splitext(playbook)[0]
                                       for playbook in locate_workflows_in_directory(core.config.paths.workflows_path)]
                    if playbook_name in saved_playbooks:
                        os.rename(os.path.join(core.config.paths.workflows_path, '{0}.workflow'.format(playbook_name)),
                                  os.path.join(core.config.paths.workflows_path, '{0}.workflow'.format(new_name)))
                    return json.dumps({"status": 'success',
                                       "playbooks": running_context.controller.get_all_workflows()})
                else:
                    return json.dumps({"status": 'error: no name provided',
                                       "playbooks": running_context.controller.get_all_workflows()})
            else:
                return json.dumps({"status": 'error: invalid form',
                                   "playbooks": running_context.controller.get_all_workflows()})
        else:
            return json.dumps({"status": 'error: playbook name not found',
                               "playbooks": running_context.controller.get_all_workflows()})
    elif action == 'delete':
        status = 'success'
        if running_context.controller.is_playbook_registerd(playbook_name):
            running_context.controller.remove_playbook(playbook_name)
        if playbook_name in [os.path.splitext(playbook)[0] for playbook in locate_workflows_in_directory()]:
            try:
                os.remove(os.path.join(core.config.paths.workflows_path, '{0}.workflow'.format(playbook_name)))
            except OSError as e:
                status = 'error: error occurred while remove playbook file: {0}'.format(e)

        return json.dumps({'status': status, 'playbooks': running_context.controller.get_all_workflows()})
    else:
        return json.dumps({"status": 'error: invalid operation'})


def add_default_template(playbook_name, workflow_name):
    running_context.controller.create_workflow_from_template(playbook_name=playbook_name,
                                                             workflow_name=workflow_name)


@app.route("/playbook/<string:playbook_name>/<string:workflow_name>/<string:action>", methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles["/workflow"])
def workflow(playbook_name, workflow_name, action):
    if action == 'add':
        form = forms.AddWorkflowForm(request.form)
        if form.validate():
            status = 'success'
            template_playbook = form.playbook.data
            template = form.template.data
            if template and template_playbook:
                if template_playbook in [os.path.splitext(workflow)[0]
                                         for workflow in
                                         locate_workflows_in_directory(core.config.paths.templates_path)]:
                    res = running_context.controller.create_workflow_from_template(playbook_name=playbook_name,
                                                                                   workflow_name=workflow_name,
                                                                                   template_playbook=template_playbook,
                                                                                   template_name=template)
                    if not res:
                        add_default_template(playbook_name, workflow_name)
                        status = 'warning: template not found in playbook. Using default template'
                else:
                    add_default_template(playbook_name, workflow_name)
                    status = 'warning: template playbook not found. Using default template'
            else:
                add_default_template(playbook_name, workflow_name)
            if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
                workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
                return json.dumps({'workflow': {'name': workflow_name,
                                                'steps': workflow.get_cytoscape_data(),
                                                'options': workflow.options.as_json()},
                                   'status': status})
            else:
                return json.dumps({'status': 'error: could not add workflow'})
        else:
            return json.dumps({'status': 'error: invalid form'})

    elif action == 'edit':
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            form = forms.EditPlayNameForm(request.form)
            if form.validate():
                enabled = form.enabled.data if form.enabled.data else False
                scheduler = {'type': form.scheduler_type.data if form.scheduler_type.data else 'chron',
                             'autorun': str(form.autoRun.data).lower() if form.autoRun.data else 'false',
                             'args': json.loads(form.scheduler_args.data) if form.scheduler_args.data else {}}
                running_context.controller.get_workflow(playbook_name, workflow_name).options = \
                    Options(scheduler=scheduler, enabled=enabled)
                if form.new_name.data:
                    running_context.controller.update_workflow_name(playbook_name,
                                                                    workflow_name,
                                                                    playbook_name,
                                                                    form.new_name.data)
                    workflow_name = form.new_name.data
                workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
                if workflow:
                    return json.dumps({'workflow': {'name': workflow_name, 'options': workflow.options.as_json()},
                                       'status': 'success'})
                else:
                    json.dumps({'status': 'error: altered workflow can no longer be located'})
            else:
                return json.dumps({'status': 'error: invalid form'})
        else:
            return json.dumps({'status': 'error: workflow name is not valid'})

    elif action == 'save':
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            if request.get_json():
                if 'cytoscape' in request.get_json():
                    workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
                    workflow.from_cytoscape_data(json.loads(request.get_json()['cytoscape']))
                    try:
                        write_format = 'w' if sys.version_info[0] == 2 else 'wb'
                        workflow_filename = os.path.join(core.config.paths.workflows_path,
                                                         '{0}.workflow'.format(playbook_name))
                        with open(workflow_filename, write_format) as workflow_out:
                            xml = ElementTree.tostring(running_context.controller.playbook_to_xml(playbook_name))
                            workflow_out.write(xml)
                        return json.dumps({"status": "success", "steps": workflow.get_cytoscape_data()})
                    except (OSError, IOError) as e:
                        return json.dumps(
                            {"status": "Error saving: {0}".format(e.message),
                             "steps": workflow.get_cytoscape_data()})
                else:
                    return json.dumps({"status": "error: malformed json"})
            else:
                return json.dumps({"status": "error: no information received"})
        else:
            return json.dumps({'status': 'error: workflow name is not valid'})

    elif action == 'delete':
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            running_context.controller.removeWorkflow(playbook_name, workflow_name)
            status = 'success'
        else:
            status = 'error: invalid workflow name'
        return json.dumps({"status": status,
                           "playbooks": running_context.controller.get_all_workflows()})

    elif action == 'execute':
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            running_context.controller.executeWorkflow(playbook_name, workflow_name)
            status = 'success'
        else:
            status = 'error: invalid workflow name'
        return json.dumps({"status": status})

    else:
        return json.dumps({"status": 'error: invalid operation'})


@app.route('/flags', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles['/workflow'])
def display_flags():
    core.config.config.load_function_info()
    return json.dumps({"status": "success",
                       "flags": core.config.config.function_info['flags']})


@app.route('/filters', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles['/workflow'])
def display_filters():
    return json.dumps({"status": "success",
                       "filters": core.config.config.function_info['filters']})


@app.route('/cases', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def display_cases():
    return json.dumps(case_database.case_db.cases_as_json())


@app.route('/cases/<string:case_name>/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def crud_case(case_name, action):
    if action == 'add':
        case = CaseSubscriptions()
        add_cases({"{0}".format(str(case_name)): case})
        return json.dumps(case_subscription.subscriptions_as_json())
    elif action == 'delete':
        delete_cases([case_name])
        return json.dumps(case_subscription.subscriptions_as_json())
    elif action == 'edit':
        form = forms.EditCaseForm(request.form)
        if form.validate():
            if form.name.data:
                rename_case(case_name, form.name.data)
                if form.note.data:
                    case_database.case_db.edit_case_note(form.name.data, form.note.data)
            elif form.note.data:
                case_database.case_db.edit_case_note(case_name, form.note.data)
            return json.dumps(case_database.case_db.cases_as_json())
    else:
        return json.dumps({"status": "Invalid operation {0}".format(action)})


@app.route('/cases/<string:case_name>', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def display_case(case_name):
    case = case_database.case_db.session.query(case_database.Case) \
        .filter(case_database.Case.name == case_name).first()
    if case:
        return json.dumps({'case': case.as_json()})
    else:
        return json.dumps({'status': 'Case with given name does not exist'})


@app.route('/cases/event/<int:event_id>/edit', methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def edit_event_note(event_id):
    form = forms.EditEventForm(request.form)
    if form.validate():
        if form.note.data:
            valid_event_id = case_database.case_db.session.query(case_database.Event) \
                .filter(case_database.Event.id == event_id).all()
            if valid_event_id:
                case_database.case_db.edit_event_note(event_id, form.note.data)
                return json.dumps(case_database.case_db.event_as_json(event_id))
            else:
                return json.dumps({"status": "invalid event"})
    else:
        return json.dumps({"status": "Invalid form"})


@app.route('/cases/subscriptions/available', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def display_possible_subscriptions():
    with open(os.path.join('.', 'data', 'events.json')) as f:
        return f.read()


@app.route('/cases/subscriptions/<string:case_name>/global/edit', methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def edit_global_subscription(case_name):
    form = forms.EditGlobalSubscriptionForm(request.form)
    if form.validate():
        global_sub = case_subscription.GlobalSubscriptions(controller=form.controller.data,
                                                           workflow=form.workflow.data,
                                                           step=form.step.data,
                                                           next_step=form.next_step.data,
                                                           flag=form.flag.data,
                                                           filter=form.filter.data)
        success = case_subscription.edit_global_subscription(case_name, global_sub)
        if success:
            return json.dumps(case_subscription.subscriptions_as_json())
        else:
            return json.dumps({"status": "Error: Case name {0} was not found".format(case_name)})
    else:
        return json.dumps({"status": "Error: form invalid"})


@app.route('/cases/subscriptions/<string:case_name>/subscription/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def crud_subscription(case_name, action):
    if action == 'edit':
        form = forms.EditSubscriptionForm(request.form)
        if form.validate():
            success = case_subscription.edit_subscription(case_name, form.ancestry.data, form.events.data)
            if success:
                return json.dumps(case_subscription.subscriptions_as_json())
            else:
                return json.dumps({"status": "Error occurred while editing subscription"})
        else:
            return json.dumps({"status": "Error: Case name {0} was not found".format(case_name)})
    elif action == 'add':
        form = forms.AddSubscriptionForm(request.form)
        if form.validate():
            case_subscription.add_subscription(case_name, form.ancestry.data, form.events.data)
            return json.dumps(case_subscription.subscriptions_as_json())
    elif action == 'delete':
        form = forms.DeleteSubscriptionForm(request.form)
        if form.validate():
            case_subscription.remove_subscription_node(case_name, form.ancestry.data)
            return json.dumps(case_subscription.subscriptions_as_json())


@app.route('/cases/subscriptions/', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def display_subscriptions():
    return json.dumps(case_subscription.subscriptions_as_json())


@app.route("/configuration/<string:key>", methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def config_values(key):
    if current_user.is_authenticated and key:
        if hasattr(core.config.config, key):
            return json.dumps({str(key): str(getattr(core.config.config, key))})
        elif hasattr(core.config.paths, key):
            return json.dumps({str(key): str(getattr(core.config.paths, key))})
        else:
            return json.dumps({str(key): "Error: key not found"})
    else:
        return json.dumps({str(key): "Error: user is not authenticated or key is empty"})


@app.route("/configuration/set", methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def set_configuration():
    if current_user.is_authenticated:
        form = forms.SettingsForm(request.form)
        if form.validate():
            for key, value in form.data.items():
                if hasattr(core.config.paths, key):
                    setattr(core.config.paths, key, value)
                else:
                    setattr(core.config.config, key, value)
            return json.dumps({"status": 'success'})
        else:
            return json.dumps({"status": 'error: invalid form'})
    else:
        return json.dumps({"status": 'error: user is not authenticated'})


# Returns System-Level Interface Pages
@app.route('/interface/<string:name>/display', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/interface"])
def systemPages(name):
    if current_user.is_authenticated and name:
        args = getattr(interface, name)()
        return render_template("pages/" + name + "/index.html", **args)
    else:
        return {"status": "Could Not Log In."}


# Controls execution triggers
@app.route('/execution/scheduler/<string:action>', methods=["POST"])
@auth_token_required
# @roles_accepted(*userRoles["/execution/listener"])
def schedulerActions(action):
    if action == "start":
        status = running_context.controller.start()
        return json.dumps({"status": status})
    elif action == "stop":
        status = running_context.controller.stop()
        return json.dumps({"status": status})
    elif action == "pause":
        status = running_context.controller.pause()
        return json.dumps({"status": status})
    return json.dumps({"status": "invalid command"})


# Controls execution triggers
@app.route('/execution/scheduler/jobs', methods=["POST"])
@auth_token_required
# @roles_accepted(*userRoles["/execution/listener"])
def scheduler():
    return running_context.controller.getScheduledJobs()


# Controls execution triggers
@app.route('/execution/listener', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/execution/listener"])
def listener():
    form = forms.incomingDataForm(request.form)
    listener_output = Triggers.execute(form.data.data) if form.validate() else {}
    return json.dumps(listener_output)


@app.route('/execution/listener/triggers', methods=["GET"])
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
    result = str(User.query.all())
    return result


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
@app.route('/configuration/<string:app>/devices', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def listDevices(app):
    query = running_context.Device.query.all()
    output = []
    if query:
        for device in query:
            for app_elem in device.apps:
                if app_elem.app == app:
                    output.append(device.as_json())
    return json.dumps(output)


# Controls the non-specific app device configuration
@app.route('/configuration/<string:app>/devices/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def configDevicesConfig(app, action):
    if action == "add":
        form = forms.AddNewDeviceForm(request.form)
        if form.validate():
            if len(running_context.Device.query.filter_by(name=form.name.data).all()) > 0:
                return json.dumps({"status": "device could not be added"})

            running_context.Device.add_device(name=form.name.data, username=form.username.data,
                                              password=form.pw.data, ip=form.ipaddr.data, port=form.port.data,
                                              app_server=app,
                                              extraFields=form.extraFields.data)
            return json.dumps({"status": "device successfully added"})
        return json.dumps({"status": "device could not be added"})
    if action == "all":
        query = running_context.App.query.filter_by(name=app).first()
        output = []
        if query:
            for device in query.devices:
                output.append(device.as_json())

            return json.dumps(output)
    return json.dumps({"status": "could not display all devices"})


# Controls the specific app device configuration
@app.route('/configuration/<string:app>/devices/<string:device>/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def configDevicesConfigId(app, device, action):
    if action == "display":
        dev = running_context.Device.query.filter_by(name=device).first()
        if dev is not None:
            return json.dumps(dev.as_json())
        return json.dumps({"status": "could not display device"})

    elif action == "remove":
        dev = running_context.Device.query.filter_by(name=device).first()
        if dev is not None:
            dev.delete()
            db.session.commit()
            return json.dumps({"status": "removed device"})
        return json.dumps({"status": "could not remove device"})

    elif action == "edit":
        form = forms.EditDeviceForm(request.form)
        dev = running_context.Device.query.filter_by(name=device).first()
        if form.validate() and dev is not None:
            # Ensures new name is unique
            # if len(devClass.query.filter_by(name=str(device)).all()) > 0:
            #     return json.dumps({"status": "device could not be edited"})

            dev.editDevice(form)

            db.session.commit()
            return json.dumps({"status": "device successfully edited"})
        return json.dumps({"status": "device could not be edited"})


# Start Flask
def start(config_type=None):
    global db, env

    if core.config.config.https.lower() == "true":
        # Sets up HTTPS
        if core.config.config.tls_version == "1.2":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        elif core.config.config.tls_version == "1.1":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        # Provide user with informative error message
        displayIfFileNotFound(core.config.paths.certificate_path)
        displayIfFileNotFound(core.config.paths.private_key_path)

        context.load_cert_chain(core.config.paths.certificate_path, core.config.paths.private_key_path)
        app.run(debug=core.config.config.debug, ssl_context=context,
                host=core.config.config.host, port=int(core.config.config.port), threaded=True)
    else:
        app.run(debug=core.config.config.debug, host=core.config.config.host,
                port=int(core.config.config.port), threaded=True)


def displayIfFileNotFound(filepath):
    if not os.path.isfile(filepath):
        print("File not found: " + filepath)
