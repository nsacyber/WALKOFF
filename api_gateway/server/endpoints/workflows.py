import json
from io import BytesIO
from uuid import uuid4

from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy import exists, and_
from sqlalchemy.exc import IntegrityError, StatementError

from api_gateway.executiondb.workflow import Workflow, WorkflowSchema
from api_gateway.helpers import regenerate_workflow_ids
# from api_gateway.helpers import strip_device_ids, strip_argument_ids
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, validate_resource_exists_factory, is_valid_uid, \
    paginate
from api_gateway.server.problem import Problem, unique_constraint_problem, improper_json_problem, invalid_input_problem
from http import HTTPStatus

workflow_schema = WorkflowSchema()


def does_workflow_exist(workflow_id):
    return current_app.running_context.execution_db.session.query(
        exists().where(and_(Workflow.id_ == workflow_id)).scalar())


def workflow_getter(workflow_id):
    return current_app.running_context.execution_db.session.query(Workflow).filter_by(id_=workflow_id).first()


with_workflow = with_resource_factory('workflow', workflow_getter, validator=is_valid_uid)
validate_workflow_is_registered = validate_resource_exists_factory('workflow', does_workflow_exist)

ALLOWED_EXTENSIONS = {'json'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['create']))
def create_workflow():
    data = request.get_json()
    workflow_id = request.args.get("source")
    workflow_name = data['name']

    if workflow_id:
        return copy_workflow(workflow_id=workflow_id)

    if request.files and 'file' in request.files:
        data = json.loads(request.files['file'].read().decode('utf-8'))

    try:
        workflow = workflow_schema.load(data)
        current_app.running_context.execution_db.session.add(workflow)
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f"Created Workflow {workflow.name} ({workflow.id_})")
        return workflow_schema.dump(workflow), HTTPStatus.CREATED
    except ValidationError as e:
        current_app.running_context.execution_db.session.rollback()
        return improper_json_problem('workflow', 'create', workflow_name, e.messages)
    except IntegrityError:  # ToDo: Make sure this fires on duplicate
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem('workflow', 'create', workflow_name)


@with_workflow('read', 'workflow_id')
def copy_workflow(workflow_id):
    data = request.get_json()

    workflow_json = workflow_schema.dump(workflow_id)
    workflow_json['name'] = data.get("name", f"{workflow_id.name}_copy")

    regenerate_workflow_ids(workflow_json)
    try:
        new_workflow = workflow_schema.load(workflow_json)
        current_app.running_context.execution_db.session.add(new_workflow)
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f"Workflow {workflow_id.id_} copied to {new_workflow.id_}")
        return workflow_schema.dump(new_workflow), HTTPStatus.CREATED
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        current_app.logger.error(f"Could not copy workflow {workflow_json['name']}. Unique constraint failed")
        return unique_constraint_problem('workflow', 'copy', workflow_json['name'])


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
@paginate(workflow_schema)
def read_all_workflows():
    r = current_app.running_context.execution_db.session.query(Workflow).order_by(Workflow.name).all()
    for workflow in r:
        workflow_schema.dump(workflow)
    return r, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['read']))
@with_workflow('read', 'workflow_id')
def read_workflow(workflow_id):
    workflow_json = workflow_schema.dump(workflow_id)
    if request.args.get('mode') == "export":
        f = BytesIO()
        f.write(json.dumps(workflow_json, sort_keys=True, indent=4, separators=(',', ': ')).encode('utf-8'))
        f.seek(0)
        return send_file(f, attachment_filename=workflow_id.name + '.json', as_attachment=True), HTTPStatus.OK
    else:
        return workflow_json, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['update']))
@with_workflow('update', 'workflow_id')
def update_workflow(workflow_id):
    data = request.get_json()
    errors = workflow_schema.load(data, instance=workflow_id).errors
    if errors:
        return invalid_input_problem("workflow", "update", data["name"], errors)
    try:
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f"Updated workflow {workflow_id.name} ({workflow_id.id_})")
        return workflow_schema.dump(workflow_id), HTTPStatus.OK
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem('workflow', 'update', workflow_id.id_)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('workflows', ['delete']))
@with_workflow('delete', 'workflow_id')
def delete_workflow(workflow_id):
    current_app.running_context.execution_db.session.delete(workflow_id)
    current_app.logger.info(f"Removed workflow {workflow_id.name} ({workflow_id.id_})")
    current_app.running_context.execution_db.session.commit()
    return None, HTTPStatus.NO_CONTENT
