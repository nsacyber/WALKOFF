import json
import os

from flask import request, current_app
from flask_jwt_extended import jwt_required

import core.case.database as case_database
import core.config.config
import core.config.paths
from core import helpers
from core.case.workflowresults import WorkflowResult
from core.helpers import UnknownAppAction, UnknownApp, InvalidArgument
from server.returncodes import *
from server.security import roles_accepted_for_resources
import server.workflowresults  # do not delete needed to register callbacks


def get_playbooks(full=None):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        playbooks = running_context.controller.get_all_workflows(full_representation=bool(full))
        return sorted(playbooks, key=(lambda playbook: playbook['name'].lower())), SUCCESS

    return __func()


def create_playbook():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        data = request.get_json()
        playbook_name = data['name']
        if running_context.controller.is_playbook_registered(playbook_name):
            return {"error": "Playbook already exists."}, OBJECT_EXISTS_ERROR
        running_context.controller.create_playbook(playbook_name)
        current_app.logger.info('Playbook {0} created'.format(playbook_name))
        return running_context.controller.get_all_workflows(), OBJECT_CREATED

    return __func()


def read_playbook(playbook_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        if playbook_name == "templates":
            templates = {os.path.splitext(workflow)[0]:
                             helpers.get_workflow_names_from_file(
                                 os.path.join(core.config.paths.templates_path, workflow))
                         for workflow in helpers.locate_playbooks_in_directory(core.config.paths.templates_path)}
            return templates, SUCCESS
        else:
            try:
                playbooks = running_context.controller.get_all_workflows()
                playbook = next((playbook for playbook in playbooks if playbook['name'] == playbook_name), None)
                if playbook is not None:
                    return playbook['workflows'], SUCCESS
                else:
                    current_app.logger.error('Playbook {0} was not found'.format(playbook_name))
                    return {"error": "Playbook does not exist."}, OBJECT_DNE_ERROR
            except Exception as e:
                return {"error": "{0}".format(e)}, INVALID_INPUT_ERROR

    return __func()


def update_playbook():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        data = request.get_json()
        playbook_name = data['name']
        if running_context.controller.is_playbook_registered(playbook_name):
            if 'new_name' in data and data['new_name']:

                if running_context.controller.is_playbook_registered(data['new_name']):
                    current_app.logger.warning(
                        'Could not update playbook {0}. Playbook already exists.'.format(playbook_name))
                    return {"error": "Playbook already exists."}, OBJECT_EXISTS_ERROR

                new_name = data['new_name']
                running_context.controller.update_playbook_name(playbook_name, new_name)
                running_context.Triggers.update_playbook(old_playbook=playbook_name, new_playbook=new_name)
                saved_playbooks = [os.path.splitext(playbook)[0]
                                   for playbook in
                                   helpers.locate_playbooks_in_directory(core.config.paths.workflows_path)]
                if playbook_name in saved_playbooks:
                    os.rename(os.path.join(core.config.paths.workflows_path, '{0}.playbook'.format(playbook_name)),
                              os.path.join(core.config.paths.workflows_path, '{0}.playbook'.format(new_name)))
                current_app.logger.info('Playbook renamed from {0} to {1}'.format(playbook_name, new_name))

                workflow = next(playbook for playbook in running_context.controller.get_all_workflows()
                                    if playbook['name'] == new_name)['workflows']
                return workflow, SUCCESS
            else:
                current_app.logger.error('No new name provided to update playbook')
                return {"error": 'No new name provided to update playbook.'}, INVALID_INPUT_ERROR
        else:
            current_app.logger.error('Could not edit playbook {0}. Playbook does not exist.'.format(playbook_name))
            return {"error": 'Playbook does not exist.'.format(playbook_name)}, OBJECT_DNE_ERROR
    return __func()


def delete_playbook(playbook_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        if running_context.controller.is_playbook_registered(playbook_name):
            running_context.controller.remove_playbook(playbook_name)
            current_app.logger.info('Deleted playbook {0} from controller'.format(playbook_name))
            if playbook_name in [os.path.splitext(playbook)[0] for playbook in helpers.locate_playbooks_in_directory()]:
                try:
                    os.remove(os.path.join(core.config.paths.workflows_path, '{0}.playbook'.format(playbook_name)))
                    current_app.logger.info('Deleted playbook {0} from workflow directory'.format(playbook_name))
                except (IOError, OSError) as e:
                    current_app.logger.error('Error deleting playbook {0}: {1}'.format(playbook_name, e))
                    return {'error': 'Error occurred while remove playbook file: {0}.'.format(e)}, IO_ERROR
        else:
            current_app.logger.error('Could not delete playbook {0}. Playbook does not exist.'.format(playbook_name))
            return {'error': 'Playbook does not exist.'}, OBJECT_DNE_ERROR

        return {}, SUCCESS

    return __func()


def copy_playbook(playbook_name):
    from server.context import running_context
    from server.flaskserver import write_playbook_to_file

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        if running_context.controller.is_playbook_registered(playbook_name):
            data = request.get_json()
            if 'playbook' in data and data['playbook']:
                new_playbook_name = data['playbook']
            else:
                new_playbook_name = playbook_name + "_Copy"
            if running_context.controller.is_playbook_registered(new_playbook_name):
                current_app.logger.error('Cannot copy playbook {0} to {1}. '
                                         'Name already exists'.format(playbook_name, new_playbook_name))
                return {"error": 'Playbook already exists.'}, OBJECT_EXISTS_ERROR
            else:
                running_context.controller.copy_playbook(playbook_name, new_playbook_name)
                write_playbook_to_file(new_playbook_name)
                current_app.logger.info('Copied playbook {0} to {1}'.format(playbook_name, new_playbook_name))

            return running_context.controller.get_all_workflows(), OBJECT_CREATED
        else:
            current_app.logger.error('Could not copy playbook {0}. Playbook does not exist.'.format(playbook_name))
            return {'error': 'Playbook does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def get_workflows(playbook_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        try:
            workflows = running_context.controller.get_all_workflows(full_representation=True)
            if playbook_name in workflows:
                return workflows[playbook_name], SUCCESS
            else:
                current_app.logger.error('Playbook {0} not found. Cannot be displayed'.format(playbook_name))
                return {"error": "Playbook does not exist."}, OBJECT_DNE_ERROR
        except Exception as e:
            return {"error": "{0}".format(e)}, INVALID_INPUT_ERROR

    return __func()


def create_workflow(playbook_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        data = request.get_json()
        workflow_name = data['name']

        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            current_app.logger.warning('Could not create workflow {0}. Workflow already exists.'.format(workflow_name))
            return {"error": "Workflow already exists."}, OBJECT_EXISTS_ERROR

        running_context.controller.create_workflow(playbook_name, workflow_name)
        current_app.logger.info('Workflow {0}-{1} created'.format(playbook_name, workflow_name))
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
            return workflow.read(), OBJECT_CREATED
        else:
            current_app.logger.error('Could not add workflow {0}-{1}'.format(playbook_name, workflow_name))
            return {'error': 'Could not add workflow.'}, INVALID_INPUT_ERROR

    return __func()


def read_workflow(playbook_name, workflow_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
            return workflow.read(), SUCCESS
        else:
            current_app.logger.error('Workflow {0}-{1} not found. Cannot be displayed.'.format(playbook_name,
                                                                                               workflow_name))
            return {'error': 'Playbook or workflow does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def update_workflow(playbook_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        data = request.get_json()
        wf_name = data['name']
        if running_context.controller.is_workflow_registered(playbook_name, wf_name):
            if 'new_name' in data and data['new_name']:
                if running_context.controller.is_workflow_registered(playbook_name, data['new_name']):
                    current_app.logger.warning(
                        'Could not update workflow {0}. Workflow already exists.'.format(wf_name))
                    return {"error": "Workflow already exists."}, OBJECT_EXISTS_ERROR
                else:
                    running_context.controller.update_workflow_name(playbook_name,
                                                                    wf_name,
                                                                    playbook_name,
                                                                    data['new_name'])
                    running_context.Triggers.update_workflow(old_workflow=wf_name, new_workflow=data['new_name'])
                    wf_name = data['new_name']
            workflow = running_context.controller.get_workflow(playbook_name, wf_name)
            if workflow:
                current_app.logger.info('Updated workflow {0}-{1}'.format(playbook_name, wf_name))
                return workflow.read(), SUCCESS
            else:
                current_app.logger.error('Altered workflow {0}-{1} no longer in controller'.format(playbook_name,
                                                                                                   wf_name))
                return {'error': 'Altered workflow can no longer be located.'}, INVALID_INPUT_ERROR
        else:
            current_app.logger.error(
                'Workflow {0}-{1} not found in controller. Cannot be updated.'.format(playbook_name,
                                                                                      wf_name))
            return {'error': 'Playbook or workflow does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def delete_workflow(playbook_name, workflow_name):
    from server.context import running_context
    from server.flaskserver import write_playbook_to_file

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            running_context.controller.remove_workflow(playbook_name, workflow_name)

            if len(running_context.controller.get_all_workflows_by_playbook(playbook_name)) == 0:
                current_app.logger.debug('Removing playbook {0} since it is empty.'.format(playbook_name))
                playbook_filename = os.path.join(core.config.paths.workflows_path, '{0}.playbook'.format(playbook_name))
                try:
                    os.remove(playbook_filename)
                except OSError:
                    current_app.logger.warning('Cannot remove playbook {0}. '
                                               'The playbook does not exist.'.format(playbook_name))

            else:
                write_playbook_to_file(playbook_name)

            current_app.logger.info('Deleted workflow {0}-{1}'.format(playbook_name, workflow_name))
            return {}, SUCCESS
        else:
            current_app.logger.info('Workflow {0}-{1} not found in controller. Cannot delete'.format(playbook_name,
                                                                                                     workflow_name))
            return {"error": 'Playbook or workflow does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def read_workflow_risk(playbook_name, workflow_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
            risk_percent = "{0:.2f}".format(workflow.accumulated_risk * 100.00)
            risk_number = str(workflow.accumulated_risk * workflow.total_risk)
            return {"risk_percent": risk_percent,
                    "risk_number": risk_number}, SUCCESS
        else:
            current_app.logger.info(
                'Workflow {0}-{1} not found in controller. Cannot retrieve risk.'.format(playbook_name,
                                                                                         workflow_name))
            return {"error": 'Playbook or workflow does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def copy_workflow(playbook_name, workflow_name):
    from server.context import running_context
    from server.flaskserver import write_playbook_to_file

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        data = request.get_json()

        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            if 'playbook' in data and data['playbook']:
                new_playbook_name = data['playbook']
            else:
                new_playbook_name = playbook_name
            if 'workflow' in data and data['workflow']:
                new_workflow_name = data['workflow']
            else:
                new_workflow_name = workflow_name + "_Copy"

            if running_context.controller.is_workflow_registered(new_playbook_name, new_workflow_name):
                current_app.logger.error('Cannot copy workflow {0}-{1} to {2}-{3}. '
                                         'Workflow already exists.'.format(workflow_name, playbook_name,
                                                                           new_workflow_name, new_playbook_name))
                return {"error": 'Playbook or workflow already exists.'}, OBJECT_EXISTS_ERROR
            else:
                running_context.controller.copy_workflow(playbook_name, new_playbook_name, workflow_name,
                                                         new_workflow_name)
                write_playbook_to_file(new_playbook_name)
                current_app.logger.info('Workflow {0}-{1} copied to {2}-{3}'.format(playbook_name, workflow_name,
                                                                                    new_playbook_name,
                                                                                    new_workflow_name))
                workflow = running_context.controller.get_workflow(new_playbook_name, new_workflow_name)
                return workflow.read(), OBJECT_CREATED
        else:
            current_app.logger.info('Workflow {0}-{1} not found in controller. Cannot copy it.'.format(playbook_name,
                                                                                                       workflow_name))
            return {"error": 'Playbook or workflow does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def execute_workflow(playbook_name, workflow_name):
    from server.context import running_context
    from server.flaskserver import write_playbook_to_file

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            write_playbook_to_file(playbook_name)
            uid = running_context.controller.execute_workflow(playbook_name, workflow_name)
            current_app.logger.info('Executed workflow {0}-{1}'.format(playbook_name, workflow_name))
            return {'id': uid}, SUCCESS_ASYNC
        else:
            current_app.logger.error(
                'Cannot execute workflow {0}-{1}. Does not exist in controller'.format(playbook_name,
                                                                                       workflow_name))
            return {"error": 'Playbook or workflow does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def pause_workflow(playbook_name, workflow_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            running_context.controller.pause_workflow(playbook_name, workflow_name)
            current_app.logger.info('Paused workflow {0}-{1}'.format(playbook_name, workflow_name))
            return {}, SUCCESS
        else:
            current_app.logger.error('Cannot pause workflow '
                                     '{0}-{1}. Does not exist in controller'.format(playbook_name, workflow_name))
            return {"error": 'Playbook or workflow does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def resume_workflow(playbook_name, workflow_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        data = request.get_json()
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            uuid = data['uuid']
            if running_context.controller.resume_workflow(playbook_name, workflow_name, uuid):
                return {}, SUCCESS
            else:
                return {"error": "Invalid UUID."}, INVALID_INPUT_ERROR
        else:
            current_app.logger.error(
                'Cannot resume workflow {0}-{1}. Does not exist in controller'.format(playbook_name, workflow_name))
            return {"error": 'Playbook or workflow does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def save_workflow(playbook_name, workflow_name):
    from server.context import running_context
    from server.flaskserver import write_playbook_to_file

    @jwt_required
    @roles_accepted_for_resources('playbooks')
    def __func():
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            workflow = running_context.controller.get_workflow(playbook_name, workflow_name)
            try:
                workflow.update_from_json(request.get_json())
            except UnknownApp as e:
                return {"error": "Unknown app {0}.".format(e.app)}, INVALID_INPUT_ERROR
            except UnknownAppAction as e:
                return {'error': 'Unknown action for app'}, INVALID_INPUT_ERROR
            except InvalidArgument as e:
                return {'error': 'Invalid input to action. Error: {0}'.format(str(e))}, INVALID_INPUT_ERROR
            else:
                try:
                    write_playbook_to_file(playbook_name)
                    current_app.logger.info('Saved workflow {0}-{1}'.format(playbook_name, workflow_name))
                    return {}, SUCCESS
                except (OSError, IOError) as e:
                    current_app.logger.info(
                        'Cannot save workflow {0}-{1} to file'.format(playbook_name, workflow_name))
                    return {"error": "Error saving: {0}".format(e.message)}, IO_ERROR
        else:
            current_app.logger.info('Cannot save workflow {0}-{1}. Workflow not in controller'.format(playbook_name,
                                                                                                      workflow_name))
            return {'error': 'Playbook or workflow does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def add_default_template(playbook_name, workflow_name):
    from server.context import running_context
    running_context.controller.create_workflow(playbook_name=playbook_name,
                                               workflow_name=workflow_name)


@jwt_required
def read_results():
    @roles_accepted_for_resources('playbooks')
    def __func():
        ret = []
        completed_workflows = [workflow.as_json() for workflow in
                               case_database.case_db.session.query(WorkflowResult).filter(
                                   WorkflowResult.status == 'completed').all()]
        for result in completed_workflows:
            if result['status'] == 'completed':
                ret.append({'name': result['name'],
                            'timestamp': result['completed_at'],
                            'result': json.dumps(result['results'])})
        return ret, SUCCESS
    return __func()


@jwt_required
def read_all_results():
    return [workflow.as_json() for workflow in
            case_database.case_db.session.query(WorkflowResult).all()], SUCCESS


def read_result(uid):

    @jwt_required
    def __func():
        workflow_result = case_database.case_db.session.query(WorkflowResult).filter(WorkflowResult.uid == uid).first()
        if workflow_result is not None:
            return workflow_result.as_json(), SUCCESS
        else:
            return {'error': 'No workflow found'}, OBJECT_DNE_ERROR
    return __func()