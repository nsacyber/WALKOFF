import json
import os
from flask import Blueprint, request, current_app
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context, write_playbook_to_file
from server import forms
from core import helpers
from core.options import Options
import core.config.config
import core.config.paths

playbook_page = Blueprint('playbook_page', __name__)
playbooks_page = Blueprint('playbooks_page', __name__)


@playbooks_page.route('', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def display_available_playbooks():
    return json.dumps({"status": "success", "playbooks": running_context.controller.get_all_workflows()})


@playbooks_page.route('/<playbook_name>', methods=['PUT'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def create_playbook(playbook_name):
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
                current_app.logger.info('Playbook {0} created from template {1}'.format(playbook_name,
                                                                                        template_playbook))
            else:
                running_context.controller.create_playbook_from_template(playbook_name=playbook_name)
                current_app.logger.info('Playbook {0} cannot be created from template {1} because it doesn\'t exist. '
                                        'Using default template instead'.format(playbook_name,template_playbook))
                status = 'warning: template playbook not found. Using default template'
        else:
            running_context.controller.create_playbook_from_template(playbook_name=playbook_name)
            current_app.logger.info('Playbook {0} created from default template'.format(playbook_name))
        return json.dumps({"status": status,
                           "playbooks": running_context.controller.get_all_workflows()})
    else:
        current_app.logger.error('Invalid form received in create_playbook')
        return json.dumps({'status': 'error: invalid form'})


@playbooks_page.route('/<playbook_name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def read_playbook_get_templates(playbook_name):
    if playbook_name == "templates":
        templates = {os.path.splitext(workflow)[0]:
                         helpers.get_workflow_names_from_file(os.path.join(core.config.paths.templates_path, workflow))
                     for workflow in helpers.locate_workflows_in_directory(core.config.paths.templates_path)}
        return json.dumps({"status": "success", "templates": templates})
    else:
        try:
            workflows = running_context.controller.get_all_workflows()
            if playbook_name in workflows:
                return json.dumps({"status": "success", "workflows": workflows[playbook_name]})
            else:
                current_app.logger.error('Playbook {0} was not found'.format(playbook_name))
                return json.dumps({"status": "error: name not found"})
        except Exception as e:
            return json.dumps({"status": "error: {0}".format(e)})


@playbooks_page.route('/<playbook_name>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def update_playbook(playbook_name):
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
                current_app.logger.info('Playbook renamed from {0} to {1}'.format(playbook_name, new_name))
                return json.dumps({"status": 'success',
                                   "playbooks": running_context.controller.get_all_workflows()})
            else:
                current_app.logger.error('No new name provided to update playbook')
                return json.dumps({"status": 'error: no name provided',
                                   "playbooks": running_context.controller.get_all_workflows()})
        else:
            current_app.logger.error('Invalid JSON provided to update playbook')
            return json.dumps({"status": 'error: invalid json',
                               "playbooks": running_context.controller.get_all_workflows()})
    else:
        current_app.logger.error('Playbook {0} is not fund. Cannot update'.format(playbook_name))
        return json.dumps({"status": 'error: playbook name not found',
                           "playbooks": running_context.controller.get_all_workflows()})


@playbooks_page.route('/<playbook_name>', methods=['DELETE'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def delete_playbook(playbook_name):
    status = 'success'
    if running_context.controller.is_playbook_registered(playbook_name):
        running_context.controller.remove_playbook(playbook_name)
        current_app.logger.info('Deleted playbook {0} from controller'.format(playbook_name))
    if playbook_name in [os.path.splitext(playbook)[0] for playbook in helpers.locate_workflows_in_directory()]:
        try:
            os.remove(os.path.join(core.config.paths.workflows_path, '{0}.workflow'.format(playbook_name)))
            current_app.logger.info('Deleted playbook {0} from workflow directory'.format(playbook_name))
        except (IOError, OSError) as e:
            current_app.logger.error('Error deleting playbook {0}: {1}'.format(playbook_name, e))
            status = 'error: error occurred while remove playbook file: {0}'.format(e)

    return json.dumps({'status': status, 'playbooks': running_context.controller.get_all_workflows()})


@playbooks_page.route('/<playbook_name>/copy', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def copy_playbook(playbook_name):
    form = forms.CopyPlaybookForm(request.form)
    if form.validate():
        if form.playbook.data:
            new_playbook_name = form.playbook.data
        else:
            new_playbook_name = playbook_name + "_Copy"

        if running_context.controller.is_playbook_registered(new_playbook_name):
            current_app.logger.error('Cannot copy playbook {0} to {1}. Name already exists'.format(playbook_name,
                                                                                                   new_playbook_name))
            status = 'error: invalid playbook name'
        else:
            running_context.controller.copy_playbook(playbook_name, new_playbook_name)
            current_app.logger.info('Copied playbook {0} to {1}'.format(playbook_name, new_playbook_name))
            status = 'success'

        return json.dumps({"status": status})


@playbooks_page.route('/<playbook_name>/workflows', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def display_workflows_for_playbook(playbook_name):
    try:
        workflows = running_context.controller.get_all_workflows()
        if playbook_name in workflows:
            return json.dumps({"status": "success", "workflows": workflows[playbook_name]})
        else:
            current_app.logger.error('Playbook {0} not found. Cannot be displayed'.format(playbook_name))
            return json.dumps({"status": "error: name not found"})
    except Exception as e:
        return json.dumps({"status": "error: {0}".format(e)})


@playbooks_page.route('/<playbook_name>/workflows/<workflow_name>', methods=['PUT'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def create_workflow(playbook_name, workflow_name):
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
                    current_app.logger.warning('Workflow {0}-{1} could not be created from template {2}-{3}. '
                                               'Using default template'.format(playbook_name, workflow_name,
                                                                               template_playbook, template))
                    status = 'warning: template not found in playbook. Using default template'
                else:
                    current_app.logger.info('Workflow {0}-{1} created from template {2}-{3}. '
                                            'Using default template'.format(playbook_name, workflow_name,
                                                                            template_playbook, template))
            else:
                add_default_template(playbook_name, workflow_name)
                current_app.logger.info('Workflow {0}-{1} could not be created from template playbook {0} '
                                        'because template playbook is not found. '
                                        'Using default template'.format(playbook_name,
                                                                        workflow_name))
                status = 'warning: template playbook not found. Using default template'
        else:
            add_default_template(playbook_name, workflow_name)
            current_app.logger.info('Workflow {0}-{1} created from default template'.format(playbook_name,
                                                                                            workflow_name))
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
            return json.dumps({'workflow': {'name': workflow_name,
                                            'steps': workflow.get_cytoscape_data(),
                                            'options': workflow.options.as_json()},
                               'status': status})
        else:
            current_app.logger.error('Could not add workflow {0}-{1}'.format(playbook_name, workflow_name))
            return json.dumps({'status': 'error: could not add workflow'})
    else:
        current_app.logger.error('Invalid form to add workflow {0}-{1}'.format(playbook_name, workflow_name))
        return json.dumps({'status': 'error: invalid form'})


@playbooks_page.route('/<playbook_name>/workflows/<workflow_name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def get_workflow(playbook_name, workflow_name):
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
                current_app.logger.error('Ancestry {0} not found in workflow '
                                         '{1}-{2}'.format(request.get_json()['ancestry'], playbook_name, workflow_name))
                return json.dumps({"status": 'error: element not found'})
        else:
            current_app.logger.error('Malformed JSON found in get_workflow: {0}'.format(request.get_json()))
            return json.dumps({"status": 'error: malformed JSON'})
    else:
        current_app.logger.error('Workflow {0}-{1} not found. Cannot be displayed.'.format(playbook_name,
                                                                                           workflow_name))
        return json.dumps({'status': 'error: name not found'})


@playbooks_page.route('/<playbook_name>/workflows/<workflow_name>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def update_workflow(playbook_name, workflow_name):
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
                returned_json = {'workflow': {'name': workflow_name, 'options': workflow.options.as_json()},
                                   'status': 'success'}
                current_app.logger.info('Updated workflow {0}-{1} to {2}'.format(playbook_name,
                                                                                 workflow_name,
                                                                                 returned_json))
                return json.dumps(returned_json)
            else:
                current_app.logger.error('Altered workflow {0}-{1} no longer in controller'.format(playbook_name,
                                                                                                   workflow_name))
                json.dumps({'status': 'error: altered workflow can no longer be located'})
        else:
            current_app.logger.error('Invalid json ecountered when updating workflow '
                                     '{0}-{1}: {2}'.format(playbook_name, workflow_name, request.get_json()))
            return json.dumps({'status': 'error: invalid json'})
    else:
        current_app.logger.error('Workflow {0}-{1} not found in controller. Cannot be updated.'.format(playbook_name,
                                                                                                       workflow_name))
        return json.dumps({'status': 'error: workflow name is not valid'})


@playbooks_page.route('/<playbook_name>/workflows/<workflow_name>', methods=['DELETE'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def delete_workflow(playbook_name, workflow_name):
    if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
        running_context.controller.remove_workflow(playbook_name, workflow_name)
        status = 'success'
        current_app.logger.info('Deleted workflow {0}-{1}'.format(playbook_name, workflow_name))
    else:
        current_app.logger.info('Workflow {0}-{1} not found in controller. Cannot delete'.format(playbook_name,
                                                                                                 workflow_name))
        status = 'error: invalid workflow name'
    return json.dumps({"status": status,
                       "playbooks": running_context.controller.get_all_workflows()})


@playbooks_page.route('/<playbook_name>/workflows/<workflow_name>/risk', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def get_workflow_risk(playbook_name, workflow_name):
    if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
        workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
        risk_percent = "{0:.2f}".format(workflow.accumulated_risk * 100.00)
        risk_number = str(workflow.accumulated_risk * workflow.total_risk)
        return json.dumps({"risk_percent": risk_percent,
                           "risk_number": risk_number})
    else:
        return json.dumps({"status": "error: workflow not found"})


@playbooks_page.route('/<playbook_name>/workflows/<workflow_name>/copy', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def copy_workflow(playbook_name, workflow_name):
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
            current_app.logger.error('Cannot copy workflow {0}-{1} to {2}-{3}. '
                                     'Workflow already exists.'.format(workflow_name, playbook_name,
                                                                       new_workflow_name, new_playbook_name))
            status = 'error: invalid playbook and/or workflow name'
        else:
            running_context.controller.copy_workflow(playbook_name, new_playbook_name, workflow_name,
                                                     new_workflow_name)
            current_app.logger.info('Workflow {0}-{1} copied to {2}-{3}'.format(playbook_name, workflow_name,
                                                                                new_playbook_name, new_workflow_name))
            status = 'success'

        return json.dumps({"status": status})


@playbooks_page.route('/<string:playbook_name>/workflows/<string:workflow_name>/execute', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def execute_workflow(playbook_name, workflow_name):
    if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
        write_playbook_to_file(playbook_name)
        running_context.controller.execute_workflow(playbook_name, workflow_name)
        current_app.logger.info('Executed workflow {0}-{1}'.format(playbook_name, workflow_name))
        status = 'success'
    else:
        current_app.logger.error('Cannot execute workflow {0}-{1}. Does not exist in controller'.format(playbook_name,
                                                                                                        workflow_name))
        status = 'error: invalid workflow name'
    return json.dumps({"status": status})


@playbooks_page.route('/<playbook_name>/workflows/<workflow_name>/pause', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def pause_workflow(playbook_name, workflow_name):
    if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
        uuid = running_context.controller.pause_workflow(playbook_name, workflow_name)
        current_app.logger.info('Paused workflow {0}-{1}'.format(playbook_name, workflow_name))
        return json.dumps({"uuid": uuid})
    else:
        current_app.logger.error('Cannot pause workflow {0}-{1}. Does not exist in controller'.format(playbook_name,
                                                                                                      workflow_name))
        status = 'error: invalid playbook and/or workflow name'
        return json.dumps({"status": status})


@playbooks_page.route('/<playbook_name>/workflows/<workflow_name>/resume', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def resume_workflow(playbook_name, workflow_name):
    form = forms.ResumeWorkflowForm(request.form)
    if form.validate():
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            uuid = form.uuid.data
            status = running_context.controller.resume_workflow(playbook_name, workflow_name, uuid)
        else:
            current_app.logger.error(
                'Cannot resume workflow {0}-{1}. Does not exist in controller'.format(playbook_name, workflow_name))
            status = 'error: invalid playbook and/or workflow name'
    else:
        current_app.logger.error(
            'Cannot resume workflow {0}-{1}. Invalid form'.format(playbook_name, workflow_name))
        status = 'error: invalid form'
    return json.dumps({"status": status})


@playbooks_page.route('/<playbook_name>/workflows/<workflow_name>/save', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/playbook'])
def save_workflow(playbook_name, workflow_name):
    if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
        if request.get_json():
            if 'cytoscape' in request.get_json():
                workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
                workflow.from_cytoscape_data(json.loads(request.get_json()['cytoscape']))
                try:
                    write_playbook_to_file(playbook_name)
                    current_app.logger.info('Saved workflow {0}-{1}'.format(playbook_name, workflow_name))
                    return json.dumps({"status": "success", "steps": workflow.get_cytoscape_data()})
                except (OSError, IOError) as e:
                    current_app.logger.info('Cannot save workflow {0}-{1} to file'.format(playbook_name, workflow_name))
                    return json.dumps(
                        {"status": "Error saving: {0}".format(e.message),
                         "steps": workflow.get_cytoscape_data()})
            else:
                current_app.logger.info('Cannot save workflow {0}-{1}. Malformed JSON'.format(playbook_name,
                                                                                              workflow_name))
                return json.dumps({"status": "error: malformed json"})
        else:
            current_app.logger.info('Cannot save workflow {0}-{1}. No JSON received'.format(playbook_name,
                                                                                            workflow_name))
            return json.dumps({"status": "error: no information received"})
    else:
        current_app.logger.info('Cannot save workflow {0}-{1}. Workflow not in controller'.format(playbook_name,
                                                                                                  workflow_name))
        return json.dumps({'status': 'error: workflow name is not valid'})


def add_default_template(playbook_name, workflow_name):
    running_context.controller.create_workflow_from_template(playbook_name=playbook_name,
                                                             workflow_name=workflow_name)
