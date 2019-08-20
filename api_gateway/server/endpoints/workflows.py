import json
from io import BytesIO
from copy import deepcopy

from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_claims
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from api_gateway import helpers
from api_gateway.executiondb.workflow import Workflow, WorkflowSchema
from api_gateway.helpers import regenerate_workflow_ids
from api_gateway.serverdb.user import User
from api_gateway.extensions import db
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, is_valid_uid, \
    paginate
from api_gateway.server.problem import unique_constraint_problem, improper_json_problem
from common.roles_helpers import auth_check, update_permissions, default_permissions
from http import HTTPStatus


import logging
logger = logging.getLogger(__name__)

workflow_schema = WorkflowSchema()


def workflow_getter(workflow):
    if helpers.validate_uuid(workflow):
        return current_app.running_context.execution_db.session.query(Workflow).filter_by(id_=workflow).first()
    else:
        return current_app.running_context.execution_db.session.query(Workflow).filter_by(name=workflow).first()


with_workflow = with_resource_factory('workflow', workflow_getter)

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

    username = get_jwt_claims().get('username', None)
    curr_user = db.session.query(User).filter(User.username == username).first()
    data.update({'creator': curr_user.id})

    # handling old WALKOFF workflow data
    try:
        new_permissions = data['permissions']
        access_level = data['access_level']
    except:
        new_permissions = []
        data['permissions'] = []
        access_level = 0
        data['access_level'] = 0

    if request.files and 'file' in request.files:
        data = json.loads(request.files['file'].read().decode('utf-8'))
    if workflow_id:
        wf = current_app.running_context.execution_db.session.query(Workflow)\
            .filter(Workflow.id_ == workflow_id).first()
        if wf.name == workflow_name:
            return unique_constraint_problem('workflow', 'create', workflow_name)

        copy_permissions = wf.permissions
        logger.info(f"what the heck, this is curr_user.id {curr_user.id}")
        return copy_workflow(workflow=wf, permissions=copy_permissions, workflow_name=workflow_name,
                             creator=curr_user.id)

    wf2 = current_app.running_context.execution_db.session.query(Workflow) \
        .filter(Workflow.id_ == data['id_']).first()
    if wf2:
        return import_workflow_and_regenerate_ids(data, curr_user.id)

    try:
        workflow = workflow_schema.load(data)
        # creator only
        if access_level == 0:
            update_permissions("workflows", str(workflow.id_),
                               new_permissions=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}],
                               creator=curr_user.id)
        # default permissions
        elif access_level == 1:
            default_permissions("workflows", str(workflow.id_), data, creator=curr_user.id)
        # user-specified permissions
        elif access_level == 2:
            update_permissions("workflows", str(workflow.id_), new_permissions=new_permissions, creator=curr_user.id)

        current_app.running_context.execution_db.session.add(workflow)
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f" Created Workflow {workflow.name} ({workflow.id_})")
        return workflow_schema.dump(workflow), HTTPStatus.CREATED
    except ValidationError as e:
        current_app.running_context.execution_db.session.rollback()
        return improper_json_problem('workflow', 'create', workflow_name, e.messages)
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem('workflow', 'create', workflow_name)


def import_workflow_and_regenerate_ids(workflow_json, creator):
    new_permissions = workflow_json['permissions']
    access_level = workflow_json['access_level']

    regenerate_workflow_ids(workflow_json)
    workflow_json['name'] = workflow_json.get("name")

    if access_level == 0:
        update_permissions("workflows", workflow_json['id_'],
                           new_permissions=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}],
                           creator=creator)
    if access_level == 1:
        default_permissions("workflows", workflow_json['id_'], data=workflow_json, creator=creator)
    elif access_level == 2:
        update_permissions("workflows", workflow_json['id_'], new_permissions=new_permissions, creator=creator)

    try:
        new_workflow = workflow_schema.load(workflow_json)
        current_app.running_context.execution_db.session.add(new_workflow)
        current_app.running_context.execution_db.session.commit()
        return workflow_schema.dump(new_workflow), HTTPStatus.CREATED
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        current_app.logger.error(f" Could not import workflow {workflow_json['name']}. Unique constraint failed")
        return unique_constraint_problem('workflow', 'import', workflow_json['name'])


@permissions_accepted_for_resources(ResourcePermissions('workflows', ['create']))
def copy_workflow(workflow, permissions, workflow_name=None, creator=None):
    old_json = workflow_schema.dump(workflow)
    workflow_json = deepcopy(old_json)

    update_check = auth_check(workflow_json["id_"], "update", "workflows")
    if (not update_check) and (workflow_json['creator'] != creator):
        return None, HTTPStatus.FORBIDDEN

    regenerate_workflow_ids(workflow_json)

    if workflow_name:
        workflow_json['name'] = workflow_name
    else:
        workflow_json['name'] = old_json.get("name")

    workflow_json['creator'] = creator
    access_level = workflow_json['access_level']
    if access_level == 0:
        update_permissions("workflows", workflow_json['id_'],
                           new_permissions=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}],
                           creator=creator)
    if access_level == 1:
        default_permissions("workflows", workflow_json['id_'], data=workflow_json, creator=creator)
    elif access_level == 2:
        update_permissions("workflows", workflow_json['id_'], new_permissions=permissions, creator=creator)

    try:
        new_workflow = workflow_schema.load(workflow_json)
        current_app.running_context.execution_db.session.add(new_workflow)
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f" Workflow {workflow.id_} copied to {new_workflow.id_}")
        return workflow_schema.dump(new_workflow), HTTPStatus.CREATED
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        current_app.logger.error(f" Could not copy workflow {workflow_json['name']}. Unique constraint failed")
        return unique_constraint_problem('workflow', 'copy', workflow_json['name'])


@jwt_required
@paginate(workflow_schema)
def read_all_workflows():
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    r = current_app.running_context.execution_db.session.query(Workflow).order_by(Workflow.name).all()
    ret = []
    for workflow in r:
        to_read = auth_check(str(workflow.id_), "read", "workflows")
        if (workflow.creator == curr_user_id) or to_read:
            workflow_schema.dump(workflow)
            ret.append(workflow)
    return ret, HTTPStatus.OK


@jwt_required
@with_workflow('read', 'workflow')
def read_workflow(workflow):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    to_read = auth_check(str(workflow.id_), "read", "workflows")
    logger.info(f"to read -> {to_read}")
    logger.info(f"workflow creator -> {workflow.creator}")
    if (workflow.creator == curr_user_id) or to_read:
        workflow_json = workflow_schema.dump(workflow)
        if request.args.get('mode') == "export":
            f = BytesIO()
            f.write(json.dumps(workflow_json, sort_keys=True, indent=4, separators=(',', ': ')).encode('utf-8'))
            f.seek(0)
            return send_file(f, attachment_filename=workflow.name + '.json', as_attachment=True), HTTPStatus.OK
        else:
            return workflow_json, HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@jwt_required
@with_workflow('update', 'workflow')
def update_workflow(workflow):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    data = request.get_json()

    new_permissions = data['permissions']
    access_level = data['access_level']

    to_update = auth_check(str(workflow.id_), "update", "workflows")
    logger.info(f"to update -> {to_update}")
    logger.info(f"workflow creator -> {workflow.creator}")
    if (workflow.creator == curr_user_id) or to_update:
        if access_level == 0:
            auth_check(str(workflow.id_), "update", "workflows",
                       updated_roles=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}])
        elif access_level == 1:
            default_permissions("workflows", str(workflow.id_), data=data)
        elif access_level == 2:
            auth_check(str(workflow.id_), "update", "workflows", updated_roles=new_permissions)

        try:
            workflow_schema.load(data, instance=workflow)
            current_app.running_context.execution_db.session.commit()
            current_app.logger.info(f"Updated workflow {workflow.name} ({workflow.id_})")
            return workflow_schema.dump(workflow), HTTPStatus.OK
        except ValidationError as e:
            current_app.running_context.execution_db.session.rollback()
            return improper_json_problem('workflow', 'update', workflow.id_, e.messages)
        except IntegrityError:  # ToDo: Make sure this fires on duplicate
            current_app.running_context.execution_db.session.rollback()
            return unique_constraint_problem('workflow', 'update', workflow.id_)
    else:
        return None, HTTPStatus.FORBIDDEN


@jwt_required
@with_workflow('delete', 'workflow')
def delete_workflow(workflow):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    to_delete = auth_check(str(workflow.id_), "delete", "workflows")
    if (workflow.creator == curr_user_id) or to_delete:
        current_app.running_context.execution_db.session.delete(workflow)
        current_app.logger.info(f"Removed workflow {workflow.name} ({workflow.id_})")
        current_app.running_context.execution_db.session.commit()
        return None, HTTPStatus.NO_CONTENT
    else:
        return None, HTTPStatus.FORBIDDEN
