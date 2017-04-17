import json
import os
import sys
import xml.dom.minidom as minidom
from xml.etree import ElementTree

from flask import render_template, request
from flask_security import login_required, auth_token_required, current_user, roles_accepted
from flask_security.utils import encrypt_password
from gevent import monkey

from copy import deepcopy
from core.controller import _WorkflowKey

import core.case.database as case_database
import core.case.subscription as case_subscription
import core.config.config
import core.config.paths
import core.filters
import core.flags
from core import helpers
from core.case.subscription import CaseSubscriptions, add_cases, delete_cases, \
    rename_case
from core.helpers import locate_workflows_in_directory
from core.helpers import combineDicts
from core.options import Options
from server.context import running_context
from . import database, appdevice
from . import forms, interface
from .app import app
from .database import User
from .triggers import Triggers

monkey.patch_all()

user_datastore = database.user_datastore

urls = ["/", "/key", "/workflow", "/configuration", "/interface", "/execution/listener", "/execution/listener/triggers",
        "/roles", "/users", "/configuration", '/cases', '/apps', "/execution/scheduler"]

default_urls = urls
userRoles = database.userRoles
database.initialize_user_roles(urls)
db = database.db


# Creates Test Data
@app.before_first_request
def create_user():
    database.db.create_all()

    if not database.User.query.first():
        admin_role = user_datastore.create_role(name="admin", description="administrator", pages=default_urls)

        u = user_datastore.create_user(email='admin', password=encrypt_password('admin'))

        user_datastore.add_role_to_user(u, admin_role)

        database.db.session.commit()

    apps = set(helpers.list_apps()) - set([app.name for app in database.db.session.query(appdevice.App).all()])
    for app_name in apps:
        database.db.session.add(appdevice.App(app=app_name, devices=[]))
    database.db.session.commit()


"""
    URLS
"""


@app.route("/")
@login_required
def default():
    if current_user.is_authenticated:
        default_page_name = "dashboard"
        args = {"apps": running_context.get_apps(), "authKey": current_user.get_auth_token(),
                "currentUser": current_user.email, "default_page": default_page_name}
        return render_template("container.html", **args)
    else:
        return {"status": "Could Not Log In."}

# Returns System-Level Interface Pages
@app.route('/interface/<string:name>/display', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/interface"])
def system_pages(name):
    if current_user.is_authenticated and name:
        args = getattr(interface, name)()
        combineDicts(args, {"authKey": current_user.get_auth_token()})
        return render_template("pages/" + name + "/index.html", **args)
    else:
        return {"status": "Could Not Log In."}


# Returns the API key for the user
@app.route('/key', methods=["GET", "POST"])
@login_required
def login_info():
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
    return json.dumps({"status": "success", "playbooks": running_context.controller.get_all_workflows()})


@app.route("/playbook/<string:name>", methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles["/workflow"])
def display_playbook_workflows(name):
    try:
        workflows = running_context.controller.get_all_workflows()
        if name in workflows:
            return json.dumps({"status": "success", "workflows": workflows[name]})
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
    return json.dumps({"status": "success", "templates": templates})


@app.route("/playbook/<string:playbook_name>/<string:workflow_name>/display", methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles["/workflow"])
def display_workflow(playbook_name, workflow_name):
    if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
        if not request.get_json():
            return json.dumps({"status": "success",
                               "steps": running_context.controller.get_workflow(playbook_name,
                                                                                workflow_name).get_cytoscape_data(),
                               'options': running_context.controller.get_workflow(playbook_name,
                                                                                  workflow_name).options.as_json()})
        elif 'ancestry' in request.get_json():
            workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
            info = workflow.get_children(request.get_json()['ancestry'])
            if info:
                return json.dumps({"status": "success", "element": info})
            else:
                return json.dumps({"status": 'error: element not found'})
        else:
            return json.dumps({"status": 'error: malformed JSON'})
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
        if running_context.controller.is_playbook_registered(playbook_name):
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
        if running_context.controller.is_playbook_registered(playbook_name):
            running_context.controller.remove_playbook(playbook_name)
        if playbook_name in [os.path.splitext(playbook)[0] for playbook in locate_workflows_in_directory()]:
            try:
                os.remove(os.path.join(core.config.paths.workflows_path, '{0}.workflow'.format(playbook_name)))
            except OSError as e:
                status = 'error: error occurred while remove playbook file: {0}'.format(e)

        return json.dumps({'status': status, 'playbooks': running_context.controller.get_all_workflows()})

    elif action == "copy":
        form = forms.CopyPlaybookForm(request.form)
        if form.validate():
            if form.playbook.data:
                new_playbook_name = form.playbook.data
            else:
                new_playbook_name = playbook_name+"_Copy"

            if running_context.controller.is_playbook_registered(new_playbook_name):
                status = 'error: invalid playbook name'
            else:
                running_context.controller.copy_playbook(playbook_name, new_playbook_name)
                status = 'success'

            return json.dumps({"status": status})
    else:
        return json.dumps({"status": 'error: invalid operation'})


def add_default_template(playbook_name, workflow_name):
    running_context.controller.create_workflow_from_template(playbook_name=playbook_name,
                                                             workflow_name=workflow_name)


def write_playbook_to_file(playbook_name):
    write_format = 'w' if sys.version_info[0] == 2 else 'wb'
    playbook_filename = os.path.join(core.config.paths.workflows_path,
                                     '{0}.workflow'.format(playbook_name))
    with open(playbook_filename, write_format) as workflow_out:
        xml = ElementTree.tostring(running_context.controller.playbook_to_xml(playbook_name))
        xml_dom = minidom.parseString(xml).toprettyxml(indent='\t')
        workflow_out.write(xml_dom.encode('utf-8'))


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
                        write_playbook_to_file(playbook_name)
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
            running_context.controller.remove_workflow(playbook_name, workflow_name)
            status = 'success'
        else:
            status = 'error: invalid workflow name'
        return json.dumps({"status": status,
                           "playbooks": running_context.controller.get_all_workflows()})

    elif action == 'execute':
        write_playbook_to_file(playbook_name)
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            running_context.controller.execute_workflow(playbook_name, workflow_name)
            status = 'success'
        else:
            status = 'error: invalid workflow name'
        return json.dumps({"status": status})

    elif action == "copy":
        form = forms.CopyWorkflowForm(request.form)
        if form.validate():
            if form.playbook.data:
                new_playbook_name = form.playbook.data
            else:
                new_playbook_name = playbook_name
            if form.workflow.data:
                new_workflow_name = form.workflow.data
            else:
                new_workflow_name = workflow_name+"_Copy"

            if running_context.controller.is_workflow_registered(new_playbook_name, new_workflow_name):
                status = 'error: invalid playbook and/or workflow name'
            else:
                running_context.controller.copy_workflow(playbook_name, new_playbook_name, workflow_name, new_workflow_name)
                status = 'success'

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


@app.route('/cases/import', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def import_cases():
    form = forms.ImportCaseForm(request.form)
    filename = form.filename.data if form.filename.data else core.config.paths.default_case_export_path
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as cases_file:
                cases_file = cases_file.read()
                cases_file = cases_file.replace('\n', '')
                cases = json.loads(cases_file)
            case_subscription.add_cases(cases)
            return json.dumps({"status": "success", "cases": case_subscription.subscriptions_as_json()})
        except (OSError, IOError):
            return json.dumps({"status": "error reading file"})
        except ValueError:
            return json.dumps({"status": "file contains invalid JSON"})
    else:
        return json.dumps({"status": "error: file does not exist"})


@app.route('/cases/export', methods=['POST'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def export_cases():
    form = forms.ExportCaseForm(request.form)
    filename = form.filename.data if form.filename.data else core.config.paths.default_case_export_path
    try:
        with open(filename, 'w') as cases_file:
            cases_file.write(json.dumps(case_subscription.subscriptions_as_json()))
        return json.dumps({"status": "success"})
    except (OSError, IOError):
        return json.dumps({"status": "error writing to file"})


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


@app.route('/cases/availablesubscriptions', methods=['GET'])
@auth_token_required
@roles_accepted(*userRoles['/cases'])
def display_possible_subscriptions():
    return json.dumps(core.config.config.possible_events)


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
        if hasattr(core.config.paths, key):
            return json.dumps({str(key): str(getattr(core.config.paths, key))})
        elif hasattr(core.config.config, key):
            return json.dumps({str(key): str(getattr(core.config.config, key))})
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
                    if key == 'workflows_path' and key != core.config.paths.workflows_path:
                        for playbook in running_context.controller.get_all_playbooks():
                            try:
                                write_playbook_to_file(playbook)
                            except (IOError, OSError):
                                pass
                        core.config.paths.workflows_path = value
                        running_context.controller.workflows = {}
                        running_context.controller.load_all_workflows_from_directory()
                    else:
                        setattr(core.config.paths, key, value)
                        if key == 'apps_path':
                            core.config.config.load_function_info()
                else:
                    setattr(core.config.config, key, value)
            return json.dumps({"status": 'success'})
        else:
            return json.dumps({"status": 'error: invalid form'})
    else:
        return json.dumps({"status": 'error: user is not authenticated'})





# Controls execution triggers
@app.route('/execution/scheduler/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/execution/scheduler"])
def scheduler_actions(action):
    if action == "start":
        status = running_context.controller.start()
        return json.dumps({"status": status})
    elif action == "stop":
        status = running_context.controller.stop()
        return json.dumps({"status": status})
    elif action == "pause":
        status = running_context.controller.pause()
        return json.dumps({"status": status})
    elif action == "resume":
        status = running_context.controller.resume()
        return json.dumps({"status": status})
    return json.dumps({"status": "invalid command"})


# Controls execution triggers
@app.route('/execution/scheduler/<string:job_id>/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/execution/scheduler"])
def scheduler_actions_by_id(job_id, action):
    if action == "pause":
        running_context.controller.pause_job(job_id)
        return json.dumps({"status": "Job Paused"})
    elif action == "resume":
        running_context.controller.resume_job(job_id)
        return json.dumps({"status": "Job Resumed"})
    return json.dumps({"status": "invalid command"})


# Controls execution triggers
@app.route('/execution/scheduler/jobs', methods=["POST"])
@auth_token_required
# @roles_accepted(*userRoles["/execution/listener"])
def scheduler():
    return running_context.controller.get_scheduled_jobs()


# Controls execution triggers
@app.route('/execution/listener', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/execution/listener"])
def listener():
    form = forms.IncomingDataForm(request.form)
    returned_json = Triggers.execute(form.data.data) if form.validate() else {}
    return json.dumps(returned_json)


@app.route('/execution/listener/triggers', methods=["GET"])
@auth_token_required
@roles_accepted(*userRoles["/execution/listener/triggers"])
def display_all_triggers():
    return json.dumps({"status": "success", "triggers": [trigger.as_json() for trigger in Triggers.query.all()]})


@app.route('/execution/listener/triggers/<string:name>/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/execution/listener/triggers"])
def trigger_functions(action, name):
    if action == "add":
        form = forms.AddNewTriggerForm(request.form)
        if form.validate():
            query = Triggers.query.filter_by(name=name).first()
            if query is None:
                try:
                    json.loads(form.conditional.data)
                    database.db.session.add(
                        Triggers(name=name,
                                 condition=form.conditional.data,
                                 playbook=form.playbook.data,
                                 workflow=form.workflow.data))

                    database.db.session.commit()
                    return json.dumps({"status": "success"})
                except ValueError:
                    return json.dumps({"status": "error: invalid json in conditional field"})
            else:
                return json.dumps({"status": "warning: trigger with that name already exists"})
        return json.dumps({"status": "error: form not valid"})

    if action == "edit":
        form = forms.EditTriggerForm(request.form)
        trigger = Triggers.query.filter_by(name=name).first()
        if form.validate() and trigger is not None:
            # Ensures new name is unique
            if form.name.data:
                if len(Triggers.query.filter_by(name=form.name.data).all()) > 0:
                    return json.dumps({"status": "error: duplicate names found. Trigger could not be edited"})

            result = trigger.edit_trigger(form)

            if result:
                db.session.commit()
                return json.dumps({"status": "success"})
            else:
                return json.dumps({"status": "error: invalid json in conditional field"})
        return json.dumps({"status": "trigger could not be edited"})

    elif action == "remove":
        query = Triggers.query.filter_by(name=name).first()
        if query:
            Triggers.query.filter_by(name=name).delete()
            database.db.session.commit()
            return json.dumps({"status": "success"})
        elif query is None:
            return json.dumps({"status": "error: trigger does not exist"})
        return json.dumps({"status": "error: could not remove trigger"})

    elif action == "display":
        query = Triggers.query.filter_by(name=name).first()
        if query:
            return json.dumps({"status": 'success', "trigger": query.as_json()})
        return json.dumps({"status": "error: trigger not found"})


# Controls roles
@app.route('/roles/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/roles"])
def role_add_actions(action):
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

                database.add_to_user_roles(n, default_urls)

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
def role_actions(action, name):
    role = database.Role.query.filter_by(name=name).first()

    if role:

        if action == "edit":
            form = forms.EditRoleForm(request.form)
            if form.validate():
                if form.description.data:
                    role.set_description(form.description.data)
                if form.pages.data:
                    database.add_to_user_roles(name, form.pages)
            return json.dumps(role.display())

        elif action == "display":
            return json.dumps(role.display())
        else:
            return json.dumps({"status": "invalid input"})

    return json.dumps({"status": "role does not exist"})


# Returns the list of all user roles
@app.route('/roles', methods=["GET"])
@auth_token_required
@roles_accepted(*userRoles["/roles"])
def display_roles():
    roles = database.Role.query.all()
    if roles:
        result = [role.name for role in roles]
        return json.dumps(result)
    else:
        return json.dumps({"status": "roles do not exist"})


# Controls non-specific users and roles
@app.route('/users/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/users"])
def user_non_specific_actions(action):
    # Adds a new user
    if action == "add":
        form = forms.NewUserForm(request.form)
        if form.validate():
            if not database.User.query.filter_by(email=form.username.data).first():
                un = form.username.data
                pw = encrypt_password(form.password.data)

                # Creates User
                u = user_datastore.create_user(email=un, password=pw)

                if form.role.data:
                    u.set_roles(form.role.data)

                has_admin = False
                for role in u.roles:
                    if role.name == "admin":
                        has_admin = True
                if not has_admin:
                    u.set_roles(["admin"])

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
def display_all_users():
    result = str(User.query.all())
    return json.dumps(result)


# Controls non-specific users and roles
@app.route('/users/<string:id_or_email>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/users"])
def display_user(id_or_email):
    user = user_datastore.get_user(id_or_email)
    if user:
        return json.dumps(user.display())
    else:
        return json.dumps({"status": "could not display user"})


# Controls users and roles
@app.route('/users/<string:id_or_email>/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/users"])
def user_actions(action, id_or_email):
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
                    user.password = encrypt_password(form.password.data)
                    database.db.session.commit()
                if form.role.data:
                    user.set_roles(form.role.data)

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
def list_devices(app):
    query = running_context.Device.query.all()
    output = []
    if query:
        for device in query:
            if app == device.app.name:
                output.append(device.as_json())
    return json.dumps(output)


# Controls the non-specific app device configuration
@app.route('/configuration/<string:app>/devices/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def config_devices_config(app, action):
    if action == "add":
        form = forms.AddNewDeviceForm(request.form)
        if form.validate():
            if len(running_context.Device.query.filter_by(name=form.name.data).all()) > 0:
                return json.dumps({"status": "device could not be added"})

            running_context.Device.add_device(name=form.name.data, username=form.username.data,
                                              password=form.pw.data, ip=form.ipaddr.data, port=form.port.data,
                                              app_server=app,
                                              extra_fields=form.extraFields.data)
            return json.dumps({"status": "device successfully added"})
        return json.dumps({"status": "device could not be added"})
    elif action == "all":
        query = running_context.App.query.filter_by(name=app).first()
        output = []
        if query:
            for device in query.devices:
                output.append(device.as_json())

            return json.dumps(output)
        return json.dumps({"status": "could not display all devices"})
    elif action == 'export':
        form = forms.ExportImportAppDevices(request.form)
        filename = form.filename.data if form.filename.data else core.config.paths.default_appdevice_export_path
        returned_json = {}
        apps = running_context.App.query.all()
        for app in apps:
            devices = []
            for device in app.devices:
                device_json = device.as_json(with_apps=False)
                device_json.pop('app', None)
                device_json.pop('id', None)
                devices.append(device_json)
            returned_json[app.as_json()['name']] = devices

        #print(json.dumps(returned_json, indent=4, sort_keys=True))

        try:
            with open(filename, 'w') as appdevice_file:
                appdevice_file.write(json.dumps(returned_json, indent=4, sort_keys=True))
        except (OSError, IOError):
            return json.dumps({"status": "error writing file"})
        return json.dumps({"status": "success"})

    elif action == "import":
        form = forms.ExportImportAppDevices(request.form)
        filename = form.filename.data if form.filename.data else core.config.paths.default_appdevice_export_path
        try:
            with open(filename, 'r') as appdevice_file:
                read_file = appdevice_file.read()
                read_file = read_file.replace('\n', '')
                appsDevices = json.loads(read_file)
        except (OSError, IOError):
            return json.dumps({"status": "error reading file"})
        for app in appsDevices:
            for device in appsDevices[app]:
                extra_fields = {}
                for key in device:
                    if key not in ["ip", "name", "port", "username"]:
                        extra_fields[key] = device[key]
                extra_fields_str = json.dumps(extra_fields)
                running_context.Device.add_device(name=device["name"], username=device["username"], ip=device["ip"], port=device["port"],
                                     extra_fields=extra_fields_str, app_server=app, password="")
        return json.dumps({"status": "success"})



# Controls the specific app device configuration
@app.route('/configuration/<string:app>/devices/<string:device>/<string:action>', methods=["POST"])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def config_devices_config_id(app, device, action):

    if action == "remove":
        dev = running_context.Device.query.filter_by(name=device).first()
        if dev is not None:
            db.session.delete(dev)
            db.session.commit()
            return json.dumps({"status": "removed device"})
        return json.dumps({"status": "could not remove device"})


# Controls the specific app device edit configuration
@app.route('/configuration/<string:app>/devices/<string:device>/<string:action>', methods=["GET"])
@auth_token_required
@roles_accepted(*userRoles["/configuration"])
def config_devices_config_id_edit(app, device, action):
    if action == "display":
        dev = running_context.Device.query.filter_by(name=device).first()
        if dev is not None:
            return json.dumps(dev.as_json())
        return json.dumps({"status": "could not display device"})
    if action == "edit":
        form = forms.EditDeviceForm(request.args)
        dev = running_context.Device.query.filter_by(name=device).first()
        if form.validate() and dev is not None:
            dev.edit_device(form)
            db.session.commit()
            return json.dumps({"status": "device successfully edited"})
        return json.dumps({"status": "device could not be edited"})


def display_if_file_not_found(filepath):
    if not os.path.isfile(filepath):
        print("File not found: " + filepath)
