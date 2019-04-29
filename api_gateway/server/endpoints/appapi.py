from copy import deepcopy
import json
import yaml
from http import HTTPStatus

from flask_jwt_extended import jwt_required
from flask import jsonify, current_app, request

from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, StatementError

from api_gateway.config import Config
from api_gateway import helpers
# ToDo: investigate why these imports are needed (AppApi will not have valid reference to actions if this isn't here
from api_gateway.executiondb.action import ActionApi
from api_gateway.executiondb.appapi import AppApi, AppApiSchema
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.problem import Problem, unique_constraint_problem, improper_json_problem, invalid_input_problem
from api_gateway.server.decorators import with_resource_factory, is_valid_uid, paginate


def app_api_getter(app_api):
    if helpers.validate_uuid4(app_api):
        return current_app.running_context.execution_db.session.query(AppApi).filter_by(id_=app_api).first()
    else:
        return current_app.running_context.execution_db.session.query(AppApi).filter_by(name=app_api).first()


app_api_schema = AppApiSchema()
with_app_api = with_resource_factory('app_api', app_api_getter)


# ToDo: App APIs should be stored in some nosql db instead to avoid this
def add_locations(app_api):
    app_name = app_api['name']
    for action in app_api.get('actions', []):
        action['location'] = f"{app_name}.{action['name']}"
        for param in action.get('parameters', []):
            param['location'] = f"{app_name}.{action['name']}:{param['name']}"
        if action.get('returns'):
            action['returns']['location'] = f"{app_name}.{action['name']}.returns"
    return app_api


def remove_locations(app_api):
    for action in app_api.get('actions', []):
        action.pop('location', None)
        for param in action.get('parameters', []):
            param.pop('location', None)
        if action.get('returns'):
            action['returns'].pop('location', None)
    return app_api


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
def read_all_app_names():
    qr = current_app.running_context.execution_db.session.query(AppApi).order_by(AppApi.name).all()
    r = [result.name for result in qr]
    return r, HTTPStatus.OK


# ToDo: Add an internal user for the Umpire and worker to access the api
@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('app_apis', ['create']))
def create_app_api():
    data = request.get_json()
    app_name = data['name']

    if request.files and 'file' in request.files:
        data = json.loads(request.files['file'].read().decode('utf-8'))

    add_locations(data)
    try:
        # ToDo: make a proper common type for this when the other components need it
        app_api = app_api_schema.load(data)
        current_app.running_context.execution_db.session.add(app_api)
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f"Created App API {app_api.name} ({app_api.id_})")
        return app_api_schema.dump(app_api), HTTPStatus.CREATED
    except ValidationError as e:
        current_app.running_context.execution_db.session.rollback()
        return improper_json_problem('app_api', 'create', app_name, e.messages)
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem('app_api', 'create', app_name)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
def read_all_app_apis():
    ret = []
    for app_api in current_app.running_context.execution_db.session.query(AppApi).order_by(AppApi.name).all():
        ret.append(remove_locations(app_api_schema.dump(app_api)))
    return ret, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
@with_app_api('read', 'app')
def read_app_api(app):
    return remove_locations(app_api_schema.dump(app)), HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('app_apis', ['update']))
@with_app_api('update', 'app')
def update_app_api(app):
    data = request.get_json()
    add_locations(data)
    try:
        app_api_schema.load(data, instance=app)
        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f"Updated app_api {app.name} ({app.id_})")
        return app_api_schema.dump(app), HTTPStatus.OK
    except IntegrityError:
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem('app_api', 'update', app.id_)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('app_apis', ['delete']))
@with_app_api('delete', 'app')
def delete_app_api(app):
    current_app.running_context.execution_db.session.delete(app)
    current_app.logger.info(f"Removed app_api {app.name} ({app.id_})")
    current_app.running_context.execution_db.session.commit()
    return None, HTTPStatus.NO_CONTENT
