import base64

from flask import current_app, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_claims
from sqlalchemy.exc import IntegrityError, StatementError
from copy import deepcopy
from uuid import uuid4


from common.config import config
from common.helpers import fernet_encrypt, fernet_decrypt
from api_gateway import helpers
from api_gateway.executiondb.global_variable import (GlobalVariable, GlobalVariableSchema,
                                                     GlobalVariableTemplate, GlobalVariableTemplateSchema)
from api_gateway.serverdb.user import User
from api_gateway.extensions import db

from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, paginate
from api_gateway.server.problem import unique_constraint_problem
from http import HTTPStatus
from common.roles_helpers import auth_check, update_permissions, default_permissions, creator_check

import logging
logger = logging.getLogger(__name__)


def global_variable_getter(global_var):
    validated_global_var = helpers.validate_uuid(global_var)
    if validated_global_var:
        return current_app.running_context.execution_db.session.query(GlobalVariable)\
            .filter_by(id_=validated_global_var).first()
    else:
        return current_app.running_context.execution_db.session.query(GlobalVariable).filter_by(name=global_var).first()


def global_variable_template_getter(global_template):
    if helpers.validate_uuid(global_template):
        return current_app.running_context.execution_db.session.query(GlobalVariableTemplate).filter_by(
            id_=global_template).first()
    else:
        return current_app.running_context.execution_db.session.query(GlobalVariableTemplate).filter_by(
            name=global_template).first()


with_global_variable = with_resource_factory("global_variable", global_variable_getter)
global_variable_schema = GlobalVariableSchema()

with_global_variable_template = with_resource_factory("global_variable_template", global_variable_template_getter)
global_variable_template_schema = GlobalVariableTemplateSchema()


@jwt_required
@paginate(global_variable_schema)
def read_all_globals():
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    key = config.get_from_file(config.ENCRYPTION_KEY_PATH, mode='rb')
    ret = []
    query = current_app.running_context.execution_db.session.query(GlobalVariable).order_by(GlobalVariable.name).all()

    if request.args.get('to_decrypt') == "false":
        return query, HTTPStatus.OK
    else:
        for global_var in query:
            to_read = auth_check(str(global_var.id_), "read", "global_variables")
            if (global_var.creator == curr_user_id) or to_read:
                temp_var = deepcopy(global_var)
                temp_var.value = fernet_decrypt(key, global_var.value)
                ret.append(temp_var)

        return ret, HTTPStatus.OK


@jwt_required
@with_global_variable("read", "global_var")
def read_global(global_var):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    global_id = str(global_var.id_)
    to_read = auth_check(global_id, "read", "global_variables")

    if (global_var.creator == curr_user_id) or to_read:
        global_json = global_variable_schema.dump(global_var)

        if request.args.get('to_decrypt') == "false":
            return jsonify(global_json), HTTPStatus.OK
        else:
            key = config.get_from_file(config.ENCRYPTION_KEY_PATH, mode='rb')
            return jsonify(fernet_decrypt(key, global_json['value'])), HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@jwt_required
@with_global_variable("delete", "global_var")
def delete_global(global_var):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    global_id = str(global_var.id_)
    to_delete = auth_check(global_id, "delete", "global_variables")

    if (global_var.creator == curr_user_id) or to_delete:
        current_app.running_context.execution_db.session.delete(global_var)
        current_app.logger.info(f"Global_variable removed {global_var.name}")
        current_app.running_context.execution_db.session.commit()
        return None, HTTPStatus.NO_CONTENT
    else:
        return None, HTTPStatus.FORBIDDEN


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["create"]))
def create_global():
    data = request.get_json()
    global_id = data.get('id_', str(uuid4()))

    username = get_jwt_claims().get('username', None)
    curr_user = db.session.query(User).filter(User.username == username).first()
    data.update({'creator': curr_user.id})

    new_permissions = data.get('permissions', None)
    access_level = data.get('access_level', 1)

    # creator only
    if access_level == 0:
        update_permissions("global_variables", global_id,
                           new_permissions=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}],
                           creator=curr_user.id)
    # default permissions
    elif access_level == 1:
        default_permissions("global_variables", global_id, data=data, creator=curr_user.id)
    # user-specified permissions
    elif access_level == 2:
        update_permissions("global_variables", global_id, new_permissions=new_permissions, creator=curr_user.id)

    # if new_permissions:
    #     update_permissions("global_variables", global_id, new_permissions=new_permissions, creator=curr_user.id)
    # else:
    #     default_permissions("global_variables", global_id, data=data, creator=curr_user.id)

    try:
        key = config.get_from_file(config.ENCRYPTION_KEY_PATH, mode='rb')
        data['value'] = fernet_encrypt(key, data['value'])
        global_variable = global_variable_schema.load(data)
        current_app.running_context.execution_db.session.add(global_variable)
        current_app.running_context.execution_db.session.commit()
        return global_variable_schema.dump(global_variable), HTTPStatus.CREATED
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem("global_variable", "create", data["name"])


@jwt_required
@with_global_variable("update", "global_var")
def update_global(global_var):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db.session.query(User).filter(User.username == username).first()).id

    data = request.get_json()
    global_id = data["id_"]

    new_permissions = data['permissions']
    access_level = data['access_level']

    to_update = auth_check(global_id, "update", "global_variables")
    if (global_var.creator == curr_user_id) or to_update:
        if access_level == 0:
            auth_check(global_id, "update", "global_variables",
                       updated_roles=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}])
        if access_level == 1:
            default_permissions("global_variables", global_id, data=data)
        elif access_level == 2:
            auth_check(global_id, "update", "global_variables", updated_roles=new_permissions)
        # if new_permissions:
        #     auth_check(global_id, "update", "global_variables", updated_roles=new_permissions)
        # else:
        #     default_permissions("global_variables", global_id, data=data)
        try:
            key = config.get_from_file(config.ENCRYPTION_KEY_PATH, mode='rb')
            data['value'] = fernet_encrypt(key, data['value'])
            global_variable_schema.load(data, instance=global_var)
            current_app.running_context.execution_db.session.commit()
            return global_variable_schema.dump(global_var), HTTPStatus.OK
        except (IntegrityError, StatementError):
            current_app.running_context.execution_db.session.rollback()
            return unique_constraint_problem("global_variable", "update", data["name"])
    else:
        return None, HTTPStatus.FORBIDDEN

# Templates


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["read"]))
@paginate(global_variable_schema)
def read_all_global_templates():
    query = current_app.running_context.execution_db.session.query(GlobalVariableTemplate).order_by(
        GlobalVariableTemplate.name).all()
    return query, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["read"]))
@with_global_variable_template("read", "global_template")
def read_global_templates(global_template):
    global_json = global_variable_template_schema.dump(global_template)
    return jsonify(global_json), HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["delete"]))
@with_global_variable_template("delete", "global_template")
def delete_global_templates(global_template):
    current_app.running_context.execution_db.session.delete(global_template)
    current_app.logger.info(f"global_variable_template removed {global_template.name}")
    current_app.running_context.execution_db.session.commit()
    return None, HTTPStatus.NO_CONTENT


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["create"]))
def create_global_templates():
    data = request.get_json()

    try:
        global_variable_template = global_variable_template_schema.load(data)
        current_app.running_context.execution_db.session.add(global_variable_template)
        current_app.running_context.execution_db.session.commit()
        return global_variable_template_schema.dump(global_variable_template), HTTPStatus.CREATED
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem("global_variable_template", "create", data["name"])


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["update"]))
@with_global_variable_template("update", "global_template")
def update_global_templates(global_template):
    data = request.get_json()
    try:
        global_variable_template_schema.load(data, instance=global_template)
        current_app.running_context.execution_db.session.commit()
        return global_variable_template_schema.dump(global_template), HTTPStatus.OK
    except (IntegrityError, StatementError):
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem("global_variable_template", "update", data["name"])
