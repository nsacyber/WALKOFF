import json
import os
from flask import Blueprint, request
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context, write_playbook_to_file
from server import forms
from core import helpers
from core.options import Options
import core.config.config
import core.config.paths

playbook_page = Blueprint('playbook_page', __name__)


@playbook_page.route('/', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def display_available_playbooks():
    return json.dumps({"status": "success", "playbooks": running_context.controller.get_all_workflows()})


@playbook_page.route('/<string:name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def display_playbook_workflows(name):
    try:
        workflows = running_context.controller.get_all_workflows()
        if name in workflows:
            return json.dumps({"status": "success", "workflows": workflows[name]})
        else:
            return json.dumps({"status": "error: name not found"})
    except Exception as e:
        return json.dumps({"status": "error: {0}".format(e)})


@playbook_page.route('/templates', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def display_available_workflow_templates():
    templates = {os.path.splitext(workflow)[0]:
                     helpers.get_workflow_names_from_file(os.path.join(core.config.paths.templates_path, workflow))
                 for workflow in helpers.locate_workflows_in_directory(core.config.paths.templates_path)}
    return json.dumps({"status": "success", "templates": templates})


@playbook_page.route('/<string:playbook_name>/<string:workflow_name>/display', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
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


@playbook_page.route('/<string:playbook_name>/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def crud_playbook(playbook_name, action):
    if action == 'add':
        form = forms.AddPlaybookForm(request.form)
        if form.validate():
            status = 'success'
            template_playbook = form.playbook_template.data
            if template_playbook:
                if template_playbook in [os.path.splitext(workflow)[0]
                                         for workflow in
                                         helpers.locate_workflows_in_directory(core.config.paths.templates_path)]:
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
            if request.get_json():
                data = request.get_json()
                if 'new_name' in data and data['new_name']:
                    new_name = data['new_name']
                    running_context.controller.update_playbook_name(playbook_name, new_name)
                    saved_playbooks = [os.path.splitext(playbook)[0]
                                       for playbook in
                                       helpers.locate_workflows_in_directory(core.config.paths.workflows_path)]
                    if playbook_name in saved_playbooks:
                        os.rename(os.path.join(core.config.paths.workflows_path, '{0}.workflow'.format(playbook_name)),
                                  os.path.join(core.config.paths.workflows_path, '{0}.workflow'.format(new_name)))
                    return json.dumps({"status": 'success',
                                       "playbooks": running_context.controller.get_all_workflows()})
                else:
                    return json.dumps({"status": 'error: no name provided',
                                       "playbooks": running_context.controller.get_all_workflows()})
            else:
                return json.dumps({"status": 'error: invalid json',
                                   "playbooks": running_context.controller.get_all_workflows()})
        else:
            return json.dumps({"status": 'error: playbook name not found',
                               "playbooks": running_context.controller.get_all_workflows()})

    elif action == 'delete':
        status = 'success'
        if running_context.controller.is_playbook_registered(playbook_name):
            running_context.controller.remove_playbook(playbook_name)
        if playbook_name in [os.path.splitext(playbook)[0] for playbook in helpers.locate_workflows_in_directory()]:
            try:
                os.remove(os.path.join(core.config.paths.workflows_path, '{0}.workflow'.format(playbook_name)))
            except OSError as e:
                status = 'error: error occurred while remove playbook file: {0}'.format(e)

        return json.dumps({'status': status, 'playbooks': running_context.controller.get_all_workflows()})

    elif action == 'copy':
        form = forms.CopyPlaybookForm(request.form)
        if form.validate():
            if form.playbook.data:
                new_playbook_name = form.playbook.data
            else:
                new_playbook_name = playbook_name + "_Copy"

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


@playbook_page.route('/<string:playbook_name>/<string:workflow_name>/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
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
                                         helpers.locate_workflows_in_directory(core.config.paths.templates_path)]:
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
            if request.get_json():
                data = request.get_json()
                if 'scheduler' in data:
                    enabled = data['scheduler']['enabled'] if 'enabled' in data['scheduler'] else False
                    scheduler = {'type': data['scheduler']['type'] if 'type' in data['scheduler'] else 'cron',
                                 'autorun': (str(data['scheduler']['autorun']).lower()
                                             if 'autorun' in data['scheduler'] else 'false'),
                                 'args': json.loads(data['scheduler']['args']) if 'args' in data['scheduler'] else {}}
                    running_context.controller.get_workflow(playbook_name, workflow_name).options = \
                        Options(scheduler=scheduler, enabled=enabled)
                if 'new_name' in data and data['new_name']:
                    running_context.controller.update_workflow_name(playbook_name,
                                                                    workflow_name,
                                                                    playbook_name,
                                                                    data['new_name'])
                    workflow_name = data['new_name']
                workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
                if workflow:
                    return json.dumps({'workflow': {'name': workflow_name, 'options': workflow.options.as_json()},
                                       'status': 'success'})
                else:
                    json.dumps({'status': 'error: altered workflow can no longer be located'})
            else:
                return json.dumps({'status': 'error: invalid json'})
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

    elif action == 'copy':
        form = forms.CopyWorkflowForm(request.form)
        if form.validate():
            if form.playbook.data:
                new_playbook_name = form.playbook.data
            else:
                new_playbook_name = playbook_name
            if form.workflow.data:
                new_workflow_name = form.workflow.data
            else:
                new_workflow_name = workflow_name + "_Copy"

            if running_context.controller.is_workflow_registered(new_playbook_name, new_workflow_name):
                status = 'error: invalid playbook and/or workflow name'
            else:
                running_context.controller.copy_workflow(playbook_name, new_playbook_name, workflow_name,
                                                         new_workflow_name)
                status = 'success'

            return json.dumps({"status": status})

    else:
        return json.dumps({"status": 'error: invalid operation'})
