from flask import current_app, request, send_file, jsonify
from flask_jwt_extended import jwt_required

from api_gateway.executiondb.global_variable import GlobalVariable
from api_gateway.executiondb.schemas import GlobalVariableSchema
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory
from api_gateway.server.problem import Problem
from api_gateway.server.returncodes import *
from itertools import islice

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def global_variable_getter(global_id):
    return current_app.running_context.execution_db.session.query(GlobalVariable).filter_by(_id=global_id).first()


with_global_variable = with_resource_factory("global_variable", global_variable_getter)
global_variable_schema = GlobalVariableSchema()


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["read"]))
def read_all_devices():
    page = request.args.get("page", 1, type=int)
    start = (page-1) * current_app.config["ITEMS_PER_PAGE"]
    stop = start + current_app.config["ITEMS_PER_PAGE"]
    global_variables = islice(current_app.running_context.execution_db.session.query(GlobalVariable).all(), start, stop)
    return [global_variable_schema.dump(global_variable) for global_variable in global_variables], SUCCESS


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["read"]))
@with_global_variable("read", "global_id")
def read_device(global_id, **kwargs):
    return global_variable_schema.dump(global_id), SUCCESS


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["delete"]))
@with_global_variable("delete", "global_id")
def delete_device(global_id, **kwargs):
    current_app.running_context.execution_db.session.delete(global_id)
    current_app.logger.info("Global_variable removed {0}".format(global_id))
    current_app.running_context.execution_db.session.commit()
    return None, NO_CONTENT


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["create"]))
def create_device():
    global_json = request.get_json()
    db_query = current_app.running_context.execution_db.session.query(GlobalVariable).filter(GlobalVariable.name == global_json['name']).first()
    if db_query is not None:
        current_app.logger.error('Could not create global variable. "{0}" already exists.'.format(global_json['name']))
        return Problem.from_crud_resource(OBJECT_EXISTS_ERROR, 'global_variable', 'create',
                                          'Global variable with name {} already exists.'.format(global_json['name']))

    global_variable = global_variable_schema.load(global_json)
    current_app.running_context.execution_db.session.add(global_variable)
    current_app.running_context.execution_db.session.commit()

    # We stored it in, let's try to get it back so the client knows its _id
    global_variable = current_app.running_context.execution_db.session.query(GlobalVariable).filter_by(name=global_json["name"]).first()
    global_json = global_variable_schema.dump(global_variable)
    return global_json, OBJECT_CREATED

@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["update"]))
@with_global_variable("update", "global_id")
def update_device(global_id, **kwargs):
    global_json = request.get_json()

    # Update the db model from our new json model
    global_id._id = global_json["_id"]
    global_id.name = global_json["name"]
    global_id.value = global_json["value"]
    global_id.description = global_json["description"]

    current_app.running_context.execution_db.session.commit()
    global_json = global_variable_schema.dump(global_variable_getter(global_json.get("_id")))
    return global_json, SUCCESS

