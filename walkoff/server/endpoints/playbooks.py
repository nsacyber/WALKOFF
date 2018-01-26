import json

from flask import request, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import exists
from sqlalchemy.exc import IntegrityError

import walkoff.case.database as case_database
import walkoff.config.paths
from walkoff.case.workflowresults import WorkflowResult
from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.decorators import validate_resource_exists_factory
import walkoff.coredb.devicedb
from walkoff.coredb.playbook import Playbook
from walkoff.coredb.workflow import Workflow
from walkoff.coredb.argument import Argument
from walkoff.helpers import InvalidExecutionElement, InvalidArgument


def does_playbook_exist(playbook_id):
    return walkoff.coredb.devicedb.device_db.session.query(exists().where(Playbook.id == playbook_id)).scalar()


def does_workflow_exist(playbook_id, workflow_id):
    return walkoff.coredb.devicedb.device_db.session.query(exists().where(Workflow.id == workflow_id)).scalar()


validate_playbook_is_registered = validate_resource_exists_factory('playbook', does_playbook_exist)
validate_workflow_is_registered = validate_resource_exists_factory('workflow', does_workflow_exist)

'''
def validate_playbook_is_registered(operation, playbook_name):
    from walkoff.server.context import running_context

    def wrapper(func):
        if running_context.controller.is_playbook_registered(playbook_name):
            return func
        else:
            current_app.logger.error(
                'Could not {0} playbook {1}. Playbook does not exist.'.format(operation, playbook_name))
            return lambda: ({"error": 'Playbook does not exist'.format(playbook_name)}, OBJECT_DNE_ERROR)

    return wrapper


def validate_workflow_is_registered(operation, playbook_name, workflow_name):
    from walkoff.server.context import running_context

    def wrapper(func):
        if running_context.controller.is_workflow_registered(playbook_name, workflow_name):
            return func
        else:
            current_app.logger.error(
                'Could not {0} workflow {1}-{2}. Workflow does not exist.'.format(
                    operation, playbook_name, workflow_name))
            return lambda: ({"error": 'Workflow does not exist'.format(playbook_name)}, OBJECT_DNE_ERROR)

    return wrapper
'''


def get_playbooks(full=None):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        full_rep = bool(full)
        playbooks = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()

        if full_rep:
            ret_playbooks = [playbook.read() for playbook in playbooks]
        else:
            ret_playbooks = []
            for playbook in playbooks:
                entry = {'id': playbook.id, 'name': playbook.name}

                workflows = []
                for workflow in playbook.workflows:
                    workflows.append({'id': workflow.id, 'name': workflow.name})
                entry['workflows'] = sorted(workflows, key=(lambda wf: workflow.name.lower()))

                ret_playbooks.append(entry)

        return sorted(ret_playbooks, key=(lambda pb: playbook.name.lower())), SUCCESS

    return __func()


def create_playbook():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['create']))
    def __func():
        data = request.get_json()
        playbook_name = data['name']

        try:
            playbook = Playbook.create(data)
            walkoff.coredb.devicedb.device_db.session.add(playbook)
            walkoff.coredb.devicedb.device_db.session.commit()
        except IntegrityError:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error('Could not create Playbook {}. Unique constraint failed'.format(playbook_name))
            return {"error": "Unique constraint failed."}, OBJECT_EXISTS_ERROR
        except ValueError as e:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error('Could not create Playbook {}. Invalid input'.format(playbook_name))
            return {"error": e.message}, INVALID_INPUT_ERROR

        current_app.logger.info('Playbook {0} created'.format(playbook_name))
        return playbook.read(), OBJECT_CREATED

    return __func()


def read_playbook(playbook_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        try:
            playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=playbook_id).first()
            if playbook is not None:
                return playbook.read(), SUCCESS
            else:
                current_app.logger.error('Playbook {0} was not found'.format(playbook_id))
                return {"error": "Playbook does not exist."}, OBJECT_DNE_ERROR
        except Exception as e:
            return {"error": "{0}".format(e)}, INVALID_INPUT_ERROR

    return __func()


def update_playbook():
    data = request.get_json()
    playbook_id = data['id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['update']))
    @validate_playbook_is_registered('edit', playbook_id)
    def __func():
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=playbook_id).first()

        if 'name' in data and playbook.name != data['name']:
            playbook.name = data['name']

        try:
            walkoff.coredb.devicedb.device_db.session.commit()
        except IntegrityError:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error('Could not update Playbook {}. Unique constraint failed'.format(playbook_id))
            return {"error": "Unique constraint failed."}, OBJECT_EXISTS_ERROR

        current_app.logger.info('Playbook {} updated'.format(playbook_id))

        return playbook.read(), SUCCESS

    return __func()


def delete_playbook(playbook_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['delete']))
    @validate_playbook_is_registered('delete', playbook_id)
    def __func():
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=playbook_id).first()
        walkoff.coredb.devicedb.device_db.session.delete(playbook)
        walkoff.coredb.devicedb.device_db.session.commit()
        current_app.logger.info('Deleted playbook {0} '.format(playbook_id))
        return {}, SUCCESS

    return __func()


def copy_playbook(playbook_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['create', 'read']))
    @validate_playbook_is_registered('copy', playbook_id)
    def __func():
        data = request.get_json()
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=playbook_id).first()

        if 'playbook' in data and data['playbook']:
            new_playbook_name = data['playbook']
        else:
            new_playbook_name = playbook_id + "_Copy"

        playbook_json = playbook.read()
        playbook_json.pop('id')

        try:
            new_playbook = Playbook.create(playbook_json)
            walkoff.coredb.devicedb.device_db.session.add(new_playbook)
            walkoff.coredb.devicedb.device_db.session.commit()
        except IntegrityError:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error('Could not copy Playbook {}. Unique constraint failed'.format(playbook_id))
            return {"error": "Unique constraint failed."}, OBJECT_EXISTS_ERROR
        except ValueError as e:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error('Could not copy Playbook {}. Invalid input'.format(playbook_id))
            return {"error": e.message}, INVALID_INPUT_ERROR

        current_app.logger.info('Copied playbook {0} to {1}'.format(playbook_id, new_playbook_name))

        return new_playbook.read(), OBJECT_CREATED

    return __func()


def get_workflows(playbook_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=playbook_id).first()
        if playbook:
            return [workflow.read() for workflow in playbook.workflows], SUCCESS
        else:
            current_app.logger.error('Playbook {0} not found. Cannot be displayed'.format(playbook_id))
            return {"error": "Playbook does not exist."}, OBJECT_DNE_ERROR

    return __func()


def create_workflow(playbook_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['create']))
    def __func():
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=playbook_id).first()

        data = request.get_json()
        workflow_name = data['name']

        try:
            workflow = Workflow.create(data)
            playbook.workflows.append(workflow)
            walkoff.coredb.devicedb.device_db.session.add(workflow)
            walkoff.coredb.devicedb.device_db.session.commit()
        except ValueError as e:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error('Could not add workflow {0}-{1}'.format(playbook_id, workflow_name))
            return {'error': e.message}, INVALID_INPUT_ERROR
        except IntegrityError:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error('Could not create workflow {}. Unique constraint failed'.format(workflow_name))
            return {"error": "Unique constraint failed."}, OBJECT_EXISTS_ERROR

        current_app.logger.info('Workflow {0}-{1} created'.format(playbook_id, workflow_name))
        return workflow.read(), OBJECT_CREATED

    return __func()


def read_workflow(playbook_id, workflow_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    @validate_workflow_is_registered('read', playbook_id, workflow_id)
    def __func():
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=workflow_id).first()
        return workflow.read(), SUCCESS

    return __func()


def update_workflow(playbook_id):
    data = request.get_json()
    workflow_id = data['id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['update']))
    @validate_workflow_is_registered('update', playbook_id, workflow_id)
    def __func():
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=workflow_id).first()

        # TODO: Come back to this...
        try:
            workflow.update(data)
        except InvalidExecutionElement as e:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error(e.message)
            return {"error": e.message}, INVALID_INPUT_ERROR

        try:
            walkoff.coredb.devicedb.device_db.session.commit()
        except IntegrityError:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error('Could not update workflow {}. Unique constraint failed'.format(workflow_id))
            return {"error": "Unique constraint failed."}, OBJECT_EXISTS_ERROR

        current_app.logger.info('Updated workflow {0}'.format(workflow_id))
        return workflow.read(), SUCCESS

    return __func()


def delete_workflow(playbook_id, workflow_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['delete']))
    @validate_workflow_is_registered('delete', playbook_id, workflow_id)
    def __func():
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=playbook_id).first()
        playbook_workflows = len(playbook.workflows) - 1
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=workflow_id).first()
        walkoff.coredb.devicedb.device_db.session.delete(workflow)

        if playbook_workflows == 0:
            current_app.logger.debug('Removing playbook {0} since it is empty.'.format(playbook_id))
            walkoff.coredb.devicedb.device_db.session.delete(playbook)

        walkoff.coredb.devicedb.device_db.session.commit()

        current_app.logger.info('Deleted workflow {0}'.format(workflow_id))
        return {}, SUCCESS

    return __func()


def copy_workflow(playbook_id, workflow_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['create', 'read']))
    @validate_workflow_is_registered('copy', playbook_id, workflow_id)
    def __func():
        data = request.get_json()

        if 'playbook' in data and data['playbook']:
            new_playbook_name = data['playbook']
        else:
            new_playbook_name = None
        if 'workflow' in data and data['workflow']:
            new_workflow_name = data['workflow']
        else:
            new_workflow_name = workflow_id + "_Copy"

        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=workflow_id).first()
        workflow_json = workflow.read()
        workflow_json.pop('id')
        workflow_json.pop('playbook_id')
        workflow_json['name'] = new_workflow_name

        new_workflow = Workflow.create(workflow_json)
        walkoff.coredb.devicedb.device_db.session.add(new_workflow)

        if new_playbook_name and walkoff.coredb.devicedb.device_db.session.query(
                exists().where(Playbook.name == new_playbook_name)).scalar():
            playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(
                name=new_playbook_name).first()
        else:
            playbook = Playbook(new_playbook_name)
            walkoff.coredb.devicedb.device_db.session.add(playbook)

        try:
            playbook.add_workflow(new_workflow)
            walkoff.coredb.devicedb.device_db.session.commit()
        except IntegrityError:
            walkoff.coredb.devicedb.device_db.session.rollback()
            current_app.logger.error('Could not copy workflow {}. Unique constraint failed'.format(new_workflow_name))
            return {"error": "Unique constraint failed."}, OBJECT_EXISTS_ERROR

        current_app.logger.info('Workflow {0} copied to {1}'.format(workflow_id, new_workflow.id))
        return new_workflow.read(), OBJECT_CREATED

    return __func()


def execute_workflow(playbook_id, workflow_id):
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @validate_workflow_is_registered('execute', playbook_id, workflow_id)
    def __func():
        data = request.get_json()
        args = data['arguments'] if 'arguments' in data else None
        start = data['start'] if 'start' in data else None

        arguments = []
        if args:
            for arg in args:
                try:
                    arguments.append(Argument.create(arg))
                except InvalidArgument:
                    current_app.logger.error('Could not execute workflow. Invalid Argument construction')
                    return {"error": "Could not execute workflow. Invalid argument construction"}, INVALID_INPUT_ERROR

        uid = running_context.controller.execute_workflow(workflow_id, start=start, start_arguments=arguments)
        current_app.logger.info('Executed workflow {0}-{1}'.format(playbook_id, workflow_id))
        return {'id': uid}, SUCCESS_ASYNC

    return __func()


def pause_workflow(playbook_id, workflow_id):
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @validate_workflow_is_registered('pause', playbook_id, workflow_id)
    def __func():
        data = request.get_json()
        execution_uid = data['id']
        status = running_context.controller.executor.get_workflow_status(execution_uid)
        if status == 1:  # WORKFLOW_RUNNING
            if running_context.controller.pause_workflow(execution_uid):
                current_app.logger.info(
                    'Paused workflow {0}-{1}:{2}'.format(playbook_id, workflow_id, execution_uid))
                return {"info": "Workflow paused"}, SUCCESS
            else:
                return {"error": "Invalid UUID."}, INVALID_INPUT_ERROR
        elif status == 2:
            return {"info": "Workflow already paused"}, SUCCESS
        elif status == 0:
            return {"error": 'Invalid UUID'}, INVALID_INPUT_ERROR
        else:
            return {"error": 'Workflow stopped or awaiting data'}, SUCCESS_WITH_WARNING

    return __func()


def resume_workflow(playbook_id, workflow_id):
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['execute']))
    @validate_workflow_is_registered('resume', playbook_id, workflow_id)
    def __func():
        data = request.get_json()
        execution_uid = data['id']
        status = running_context.controller.executor.get_workflow_status(execution_uid)
        if status == 2:  # WORKFLOW_PAUSED
            if running_context.controller.resume_workflow(execution_uid):
                current_app.logger.info(
                    'Resumed workflow {0}-{1}:{2}'.format(playbook_id, workflow_id, execution_uid))
                return {"info": "Workflow resumed"}, SUCCESS
            else:
                return {"error": "Invalid UUID."}, INVALID_INPUT_ERROR
        elif status == 1:
            return {"info": "Workflow already running"}, SUCCESS
        elif status == 0:
            return {"error": 'Invalid UUID'}, INVALID_INPUT_ERROR
        else:
            return {"error": 'Workflow stopped or awaiting data'}

    return __func()


@jwt_required
def read_results():
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
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


def read_all_results():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        return [workflow.as_json() for workflow in
                case_database.case_db.session.query(WorkflowResult).all()], SUCCESS

    return __func()


def read_result(uid):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        workflow_result = case_database.case_db.session.query(WorkflowResult).filter(WorkflowResult.uid == uid).first()
        if workflow_result is not None:
            return workflow_result.as_json(), SUCCESS
        else:
            return {'error': 'No workflow found'}, OBJECT_DNE_ERROR

    return __func()
