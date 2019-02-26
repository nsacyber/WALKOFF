import json
from io import BytesIO
from uuid import uuid4

from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy import exists, and_
from sqlalchemy.exc import IntegrityError, StatementError

from api_gateway.appgateway.apiutil import UnknownApp, UnknownFunction, InvalidParameter
# from api_gateway.executiondb.playbook import Playbook
from api_gateway.executiondb.schemas import WorkflowSchema
from api_gateway.executiondb.workflow import Workflow
from api_gateway.helpers import regenerate_workflow_ids
from api_gateway.helpers import strip_device_ids, strip_argument_ids
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, validate_resource_exists_factory, is_valid_uid
from api_gateway.server.problem import Problem
from api_gateway.server.returncodes import *

# playbook_schema = PlaybookSchema()
workflow_schema = WorkflowSchema()

invalid_execution_element_exceptions = (InvalidParameter, UnknownApp, UnknownFunction)


def does_workflow_exist(playbook_id, workflow_id):
    return current_app.running_context.execution_db.session.query(
        exists().where(and_(Workflow._id == workflow_id, Workflow.playbook_id == playbook_id))).scalar()


def playbook_getter(playbook_id):
    # playbook = current_app.running_context.execution_db.session.query(Playbook).filter_by(id=playbook_id).first()
    return None


def workflow_getter(workflow_id):
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()


with_playbook = with_resource_factory('playbook', playbook_getter, validator=is_valid_uid)
with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)
validate_workflow_is_registered = validate_resource_exists_factory('workflow', does_workflow_exist)

ALLOWED_EXTENSIONS = {'json', 'playbook'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_constraint_problem(type_, operation, id_):
    return Problem.from_crud_resource(
        OBJECT_EXISTS_ERROR,
        type_,
        operation,
        'Could not {} {} {}, possibly because of invalid or non-unique IDs.'.format(operation, type_, id_))


def improper_json_problem(type_, operation, id_, errors=None):
    return Problem.from_crud_resource(
        BAD_REQUEST,
        type_,
        operation,
        'Could not {} {} {}. Invalid JSON'.format(operation, type_, id_),
        ext={'errors': errors})


def get_playbooks(full=None):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __func():
        # full_rep = bool(full)
        # playbooks = current_app.running_context.execution_db.session.query(Playbook).all()
        #
        # if full_rep:
        #     ret_playbooks = [playbook_schema.dump(playbook) for playbook in playbooks]
        # else:
        #     ret_playbooks = []
        #     for playbook in playbooks:
        #         entry = {'id': playbook._id, 'name': playbook.name}
        #
        #         workflows = []
        #         for workflow in playbook.workflows:
        #             workflows.append({'id': workflow._id, 'name': workflow.name})
        #         entry['workflows'] = sorted(workflows, key=(lambda wf: workflow.name.lower()))
        #
        #         ret_playbooks.append(entry)
        #
        # return sorted(ret_playbooks, key=(lambda pb: pb['name'].lower())), SUCCESS
        return None
    return __func()


def create_playbook(source=None):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['create']))
    def __func():
        if request.files and 'file' in request.files:
            f = request.files['file']
            data = json.loads(f.read().decode('utf-8'))
            playbook_name = data['name'] if 'name' in data else ''
        else:
            data = request.get_json()
            playbook_name = data['name']

        try:
            # playbook = playbook_schema.load(data)

            # current_app.running_context.execution_db.session.add(playbook)
            # current_app.running_context.execution_db.session.commit()
            # current_app.logger.info('Playbook {0} created'.format(playbook_name))
            # return playbook_schema.dump(playbook), OBJECT_CREATED
            return None
        except ValidationError as e:
            current_app.running_context.execution_db.session.rollback()
            current_app.logger.error('Could not create Playbook {}. Invalid input'.format(playbook_name))
            return improper_json_problem('playbook', 'create', playbook_name, e.messages)
        except (IntegrityError, StatementError):
            current_app.running_context.execution_db.session.rollback()
            current_app.logger.error('Could not create Playbook {}. Unique constraint failed'.format(playbook_name))
            return unique_constraint_problem('playbook', 'create', playbook_name)

    if source:
        return copy_playbook(source)

    return __func()


def read_playbook(playbook_id, mode=None):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    @with_playbook('read', playbook_id)
    def __func(playbook):
        # playbook_json = playbook_schema.dump(playbook)
        # if mode == "export":
        #     strip_device_ids(playbook_json)
        #     strip_argument_ids(playbook_json)
        #     f = BytesIO()
        #     f.write(json.dumps(playbook_json, sort_keys=True, indent=4, separators=(',', ': ')).encode('utf-8'))
        #     f.seek(0)
        #     return send_file(f, attachment_filename=playbook.name + '.playbook', as_attachment=True), SUCCESS
        # else:
        #     return playbook_json, SUCCESS
        return None, SUCCESS
    return __func()


def update_playbook():
    data = request.get_json()
    playbook_id = data['id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['update']))
    @with_playbook('update', playbook_id)
    def __func(playbook):
        # if 'name' in data and playbook.name != data['name']:
        #     playbook.name = data['name']
        #
        # try:
        #     current_app.running_context.execution_db.session.commit()
        # except IntegrityError:
        #     current_app.running_context.execution_db.session.rollback()
        #     current_app.logger.error('Could not update Playbook {}. Unique constraint failed'.format(playbook_id))
        #     return unique_constraint_problem('playbook', 'update', playbook_id)
        #
        # current_app.logger.info('Playbook {} updated'.format(playbook_id))
        #
        # return playbook_schema.dump(playbook), SUCCESS
        return None, SUCCESS
    return __func()


def delete_playbook(playbook_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['delete']))
    @with_playbook('delete', playbook_id)
    def __func(playbook):
        current_app.running_context.execution_db.session.delete(playbook)
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info('Deleted playbook {0} '.format(playbook_id))
        return None, NO_CONTENT

    return __func()


def copy_playbook(playbook_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['create', 'read']))
    @with_playbook('copy', playbook_id)
    def __func(playbook):
        data = request.get_json()

        if 'name' in data and data['name']:
            new_playbook_name = data['name']
        else:
            new_playbook_name = playbook.name + "_Copy"

        # playbook_json = playbook_schema.dump(playbook)
        # playbook_json['name'] = new_playbook_name
        # playbook_json.pop('id')
        #
        # if 'workflows' in playbook_json:
        #     for workflow in playbook_json['workflows']:
        #         workflow.pop('is_valid', None)
        #         regenerate_workflow_ids(workflow)
        #
        # try:
        #     new_playbook = playbook_schema.load(playbook_json)
        #     current_app.running_context.execution_db.session.add(new_playbook)
        #     current_app.running_context.execution_db.session.commit()
        # except IntegrityError:
        #     current_app.running_context.execution_db.session.rollback()
        #     current_app.logger.error('Could not copy Playbook {}. Unique constraint failed'.format(playbook_id))
        #     return unique_constraint_problem('playbook', 'copy', playbook_id)
        # except ValueError:
        #     current_app.running_context.execution_db.session.rollback()
        #     current_app.logger.error('Could not copy Playbook {}. Invalid input'.format(playbook_id))
        #     return improper_json_problem('playbook', 'copy', playbook_id)
        #
        # current_app.logger.info('Copied playbook {0} to {1}'.format(playbook_id, new_playbook_name))
        #
        # return playbook_schema.dump(new_playbook), OBJECT_CREATED
        return None, OBJECT_CREATED
    return __func()


def get_workflows(playbook=None):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    def __get():
        return [workflow_schema.dump(workflow) for workflow in
                current_app.running_context.execution_db.session.query(Workflow).all()], SUCCESS

    if playbook:
        return get_workflows_for_playbook(playbook)
    return __get()


def get_workflows_for_playbook(playbook_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    @with_playbook('read workflows', playbook_id)
    def __func(playbook):
        return [workflow_schema.dump(workflow) for workflow in playbook.workflows], SUCCESS

    return __func()


def create_workflow(source=None):
    data = request.get_json()
    playbook_id = data.pop('playbook_id')

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['create']))
    @with_playbook('create workflow', playbook_id)
    def __func(playbook):
        workflow_name = data['name']
        if 'start' not in data:
            return Problem(BAD_REQUEST, 'Could not create workflow.', '"start" is required field.')
        try:
            workflow = workflow_schema.load(data)

            playbook.workflows.append(workflow)
            current_app.running_context.execution_db.session.add(workflow)
            current_app.running_context.execution_db.session.commit()
        except ValidationError as e:
            current_app.running_context.execution_db.session.rollback()
            current_app.logger.error('Could not create Workflow {}. Invalid input'.format(workflow_name))
            return improper_json_problem('workflow', 'create', workflow_name, e.messages)
        except IntegrityError:
            current_app.running_context.execution_db.session.rollback()
            current_app.logger.error('Could not create workflow {}. Unique constraint failed'.format(workflow_name))
            return unique_constraint_problem('workflow', 'create', workflow_name)

        current_app.logger.info('Workflow {0}-{1} created'.format(playbook_id, workflow_name))
        return workflow_schema.dump(workflow), OBJECT_CREATED

    if source:
        return copy_workflow(playbook_id, source)
    return __func()


def read_workflow(workflow_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['read']))
    @with_workflow('read', workflow_id)
    def __func(workflow):
        return workflow_schema.dump(workflow), SUCCESS

    return __func()


def update_workflow():
    data = request.get_json()
    workflow_id = data['id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['update']))
    @with_workflow('update', workflow_id)
    def __func(workflow):
        errors = workflow_schema.load(data, instance=workflow).errors
        if errors:
            return Problem.from_crud_resource(
                INVALID_INPUT_ERROR,
                'workflow',
                'update',
                'Could not update workflow {}. Invalid input.'.format(workflow_id), ext=errors)

        try:
            current_app.running_context.execution_db.session.commit()
        except IntegrityError:
            current_app.running_context.execution_db.session.rollback()
            current_app.logger.error('Could not update workflow {}. Unique constraint failed'.format(workflow_id))
            return unique_constraint_problem('workflow', 'update', workflow_id)

        current_app.logger.info('Updated workflow {0}'.format(workflow_id))
        return workflow_schema.dump(workflow), SUCCESS

    return __func()


def delete_workflow(workflow_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['delete']))
    @with_workflow('delete', workflow_id)
    def __func(workflow):
        # playbook = current_app.running_context.execution_db.session.query(Playbook).filter_by(
        #     id=workflow.playbook_id).first()
        # playbook_workflows = len(playbook.workflows) - 1
        # workflow = current_app.running_context.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()
        # current_app.running_context.execution_db.session.delete(workflow)
        #
        # if playbook_workflows == 0:
        #     current_app.logger.debug('Removing playbook {0} since it is empty.'.format(workflow.playbook_id))
        #     current_app.running_context.execution_db.session.delete(playbook)
        #
        # current_app.running_context.execution_db.session.commit()
        #
        # current_app.logger.info('Deleted workflow {0}'.format(workflow_id))
        return None, NO_CONTENT

    return __func()


def copy_workflow(playbook_id, workflow_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('playbooks', ['create', 'read']))
    @with_workflow('copy', workflow_id)
    def __func(workflow):
        data = request.get_json()

        if 'name' in data and data['name']:
            new_workflow_name = data['name']
        else:
            new_workflow_name = workflow.name + "_Copy"

        workflow_json = workflow_schema.dump(workflow)
        workflow_json.pop('id')
        workflow_json.pop('is_valid', None)
        workflow_json['name'] = new_workflow_name

        regenerate_workflow_ids(workflow_json)
        # if current_app.running_context.execution_db.session.query(exists().where(Playbook._id == playbook_id)).scalar():
        #     playbook = current_app.running_context.execution_db.session.query(Playbook).filter_by(
        #         id=playbook_id).first()
        # else:
        #     current_app.running_context.execution_db.session.rollback()
        #     current_app.logger.error('Could not copy workflow {}. Playbook does not exist'.format(playbook_id))
        #     return Problem.from_crud_resource(
        #         OBJECT_DNE_ERROR,
        #         'workflow',
        #         'copy',
        #         'Could not copy workflow {}. Playbook with id {} does not exist.'.format(workflow_id, playbook_id))

        try:

            new_workflow = workflow_schema.load(workflow_json)

            current_app.running_context.execution_db.session.add(new_workflow)
            # playbook.add_workflow(new_workflow)
            current_app.running_context.execution_db.session.commit()
        except IntegrityError:
            current_app.running_context.execution_db.session.rollback()
            current_app.logger.error('Could not copy workflow {}. Unique constraint failed'.format(new_workflow_name))
            return unique_constraint_problem('workflow', 'copy', new_workflow_name)

        current_app.logger.info('Workflow {0} copied to {1}'.format(workflow_id, new_workflow._id))
        return workflow_schema.dump(new_workflow), OBJECT_CREATED

    return __func()


def get_uuid():
    return {'uuid': str(uuid4())}, OBJECT_CREATED
