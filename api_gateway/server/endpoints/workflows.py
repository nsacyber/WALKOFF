import json
from io import BytesIO
from uuid import uuid4

from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy import exists, and_
from sqlalchemy.exc import IntegrityError, StatementError

from api_gateway.appgateway.apiutil import UnknownApp, UnknownFunction, InvalidParameter
from api_gateway.executiondb.schemas import WorkflowSchema
from api_gateway.executiondb.workflow import Workflow
from api_gateway.helpers import regenerate_workflow_ids
from api_gateway.helpers import strip_device_ids, strip_argument_ids
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, validate_resource_exists_factory, is_valid_uid
from api_gateway.server.problem import Problem
from api_gateway.server.returncodes import *

workflow_schema = WorkflowSchema()

invalid_execution_element_exceptions = (InvalidParameter, UnknownApp, UnknownFunction)


def does_workflow_exist(workflow_id):
    return current_app.running_context.execution_db.session.query(
        exists().where(and_(Workflow.id_ == workflow_id)).scalar()


def workflow_getter(workflow_id):
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()


with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)
validate_workflow_is_registered = validate_resource_exists_factory('workflow', does_workflow_exist)

ALLOWED_EXTENSIONS = {'json'}


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


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
def get_workflows():
        return [workflow_schema.dump(workflow) for workflow in
                current_app.running_context.execution_db.session.query(Workflow).all()], SUCCESS


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['create']))
@with_workflow('create workflow', 'workflow_id')
def create_workflow(workflow_id):
    data = request.get_json()
    source = request.args.get("source")

    if source:
        return copy_workflow(workflow_id.id_, source)

    workflow_name = data['name']
    if 'start' not in data:
        return Problem(BAD_REQUEST, 'Could not create workflow.', '"start" is required field.')
    try:
        workflow = workflow_schema.load(data)

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



def read_workflow(workflow_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
    @with_workflow('read', workflow_id)
    def __func(workflow):
        return workflow_schema.dump(workflow), SUCCESS

    return __func()


def update_workflow():
    data = request.get_json()
    workflow_id = data['id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('workflows', ['update']))
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
    @permissions_accepted_for_resources(ResourcePermissions('workflows', ['delete']))
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
    @permissions_accepted_for_resources(ResourcePermissions('workflows', ['create', 'read']))
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
        # if current_app.running_context.execution_db.session.query(exists().where(Playbook.id_ == playbook_id)).scalar():
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

        current_app.logger.info('Workflow {0} copied to {1}'.format(workflow_id, new_workflow.id_))
        return workflow_schema.dump(new_workflow), OBJECT_CREATED

    return __func()


def get_uuid():
    return {'uuid': str(uuid4())}, OBJECT_CREATED
