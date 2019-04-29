from flask import current_app, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError, StatementError

from api_gateway.executiondb.global_variable import (GlobalVariable, GlobalVariableSchema,
                                                     GlobalVariableTemplate, GlobalVariableTemplateSchema)
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, paginate
from api_gateway.server.problem import unique_constraint_problem
from http import HTTPStatus


def global_variable_getter(global_id):
    return current_app.running_context.execution_db.session.query(GlobalVariable).filter_by(id_=global_id).first()


def global_variable_template_getter(global_template_id):
    return current_app.running_context.execution_db.session.query(GlobalVariableTemplate).filter_by(id_=global_template_id).first()


with_global_variable = with_resource_factory("global_variable", global_variable_getter)
global_variable_schema = GlobalVariableSchema()


with_global_variable_template = with_resource_factory("global_variable_template", global_variable_template_getter)
global_variable_template_schema = GlobalVariableTemplateSchema()


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["read"]))
@paginate(global_variable_schema)
def read_all_globals():
    query = current_app.running_context.execution_db.session.query(GlobalVariable).order_by(GlobalVariable.name).all()
    return query, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["read"]))
@with_global_variable("read", "global_id")
def read_global(global_id):
    global_json = global_variable_schema.dump(global_id)
    return jsonify(global_json), HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["delete"]))
@with_global_variable("delete", "global_id")
def delete_global(global_id):
    current_app.running_context.execution_db.session.delete(global_id)
    current_app.logger.info(f"Global_variable removed {global_id.name}")
    current_app.running_context.execution_db.session.commit()
    return None, HTTPStatus.NO_CONTENT


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["create"]))
def create_global():
    data = request.get_json()
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
@with_global_variable("update", "global_id")
def update_global(global_id):
    data = request.get_json()
    try:
        global_variable_schema.load(data, instance=global_id)
        current_app.running_context.execution_db.session.commit()
        return global_variable_schema.dump(global_id), HTTPStatus.OK
    except (IntegrityError, StatementError):
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem("global_variable", "update", data["name"])


# Templates

@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["read"]))
@paginate(global_variable_schema)
def read_all_global_templates():
    query = current_app.running_context.execution_db.session.query(GlobalVariableTemplate).order_by(GlobalVariableTemplate.name).all()
    return query, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["read"]))
@with_global_variable_template("read", "global_template_id")
def read_global_templates(global_template_id):
    global_json = global_variable_template_schema.dump(global_template_id)
    return jsonify(global_json), HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["delete"]))
@with_global_variable_template("delete", "global_template_id")
def delete_global_templates(global_template_id):
    current_app.running_context.execution_db.session.delete(global_template_id)
    current_app.logger.info(f"global_variable_template removed {global_template_id.name}")
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
@with_global_variable_template("update", "global_template_id")
def update_global_templates(global_template_id):
    data = request.get_json()
    try:
        global_variable_template_schema.load(data, instance=global_template_id)
        current_app.running_context.execution_db.session.commit()
        return global_variable_template_schema.dump(global_template_id), HTTPStatus.OK
    except (IntegrityError, StatementError):
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem("global_variable_template", "update", data["name"])
