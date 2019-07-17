from flask import current_app, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_claims
from sqlalchemy.exc import IntegrityError, StatementError
from copy import deepcopy

from api_gateway import helpers
from api_gateway.executiondb.global_variable import (GlobalVariable, GlobalVariableSchema,
                                                     GlobalVariableTemplate, GlobalVariableTemplateSchema)
from api_gateway.serverdb.role import Role
from api_gateway.serverdb.user import User
from api_gateway.serverdb.resource import Permission
from api_gateway.serverdb.resource import Operation
from api_gateway.extensions import db
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, paginate
from api_gateway.server.problem import unique_constraint_problem
from http import HTTPStatus
from api_gateway.executiondb.global_variable import GlobalCipher

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
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["read"]))
@paginate(global_variable_schema)
def read_all_globals():
    f = open('/run/secrets/encryption_key')
    key = f.read()
    my_cipher = GlobalCipher(key)

    ret = []
    query = current_app.running_context.execution_db.session.query(GlobalVariable).order_by(GlobalVariable.name).all()

    if request.args.get('to_decrypt') == "false":
        return query, HTTPStatus.OK
    else:
        for global_var in query:
            temp_var = deepcopy(global_var)
            temp_var.value = my_cipher.decrypt(global_var.value)
            ret.append(temp_var)

        return ret, HTTPStatus.OK

@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["read"]))
@with_global_variable("read", "global_var")
def read_global(global_var):
    f = open('/run/secrets/encryption_key')
    key = f.read()
    my_cipher = GlobalCipher(key)

    global_json = global_variable_schema.dump(global_var)

    if request.args.get('to_decrypt') == "false":
        return jsonify(global_json), HTTPStatus.OK
    else:
        global_json['value'] = my_cipher.decrypt(global_json['value'])
        return jsonify(global_json), HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["delete"]))
@with_global_variable("delete", "global_var")
def delete_global(global_var):
    global_id = str(global_var.id_)
    logger.info(f"global_id {global_id}")
    logger.info(f"{type(global_id)}")
    to_delete = auth_check(global_id, "delete")

    if to_delete:
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
    global_id = data['id_']
    update_permissions = [("guest", ["update", "delete"])]  # data['update_permission']

    for role_elem in update_permissions:
        role_name = role_elem[0]
        role_permissions = role_elem[1]
        for resource in db.session.query(Role).filter(Role.name == role_name).first().resources:
            if resource.name == "global_variables":
                if "update" not in [elem.name for elem in resource.permissions]:
                    resource.permissions.append(Permission("update"))
                if "delete" not in [elem.name for elem in resource.permissions]:
                    resource.permissions.append(Permission("delete"))
                if resource.operations:
                    final = [Operation(global_id, role_permissions)] + resource.operations
                    setattr(resource, "operations", final)
                    logger.info(f" Newly added operation for global --> ({global_id},{role_permissions})")
                    db.session.commit()
                else:
                    resource.operations = [Operation(global_id, role_permissions)]
                    logger.info(f" Newly added operation for global --> ({global_id},{role_permissions})")
                    db.session.commit()
                logger.info(f" Updated global variable {global_id} permissions for role type {role_name}")

    try:
        global_variable = global_variable_schema.load(data)
        current_app.running_context.execution_db.session.add(global_variable)
        current_app.running_context.execution_db.session.commit()
        return global_variable_schema.dump(global_variable), HTTPStatus.CREATED
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem("global_variable", "create", data["name"])


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["update"]))
@with_global_variable("update", "global_var")
def update_global(global_var):
    # todo: ONCE UI ELEMENT IS BUILT OUT, DO CHECK FOR UPDATED PERMISSIONS
    data = request.get_json()
    global_id = data["id_"]

    to_update = auth_check(global_id, "update")
    if to_update:
        try:
            global_variable_schema.load(data, instance=global_var)
            current_app.running_context.execution_db.session.commit()
            return global_variable_schema.dump(global_var), HTTPStatus.OK
        except (IntegrityError, StatementError):
            current_app.running_context.execution_db.session.rollback()
            return unique_constraint_problem("global_variable", "update", data["name"])
    else:
        return None, HTTPStatus.FORBIDDEN


def auth_check(global_id, permission):
    username = get_jwt_claims().get('username', None)
    curr_user = db.session.query(User).filter(User.username == username).first()

    for resource in curr_user.roles[0].resources:
        if resource.name == "global_variables":
            if resource.operations:
                if global_id not in [elem.operation_id for elem in resource.operations]:
                    return False
                else:
                    for elem in resource.operations:
                        if elem.operation_id == global_id:
                            if permission not in elem.permissions_list:
                                return False
                            else:
                                return True
    return True

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
