import json

from flask import current_app, request, jsonify
from flask_jwt_extended import jwt_required

from marshmallow import ValidationError

from sqlalchemy.exc import IntegrityError, StatementError

from api_gateway.server.decorators import with_resource_factory
from api_gateway.executiondb.dashboard import Dashboard, Widget
from api_gateway.executiondb.schemas import DashboardSchema, WidgetSchema
from api_gateway.server.problem import Problem
from api_gateway.server.returncodes import *


dashboard_schema = DashboardSchema()
widget_schema = WidgetSchema()


# TODO: Add generic problems to import
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



def dashboard_getter(dashboard_id):
    return current_app.running_context.execution_db.session.query(Dashboard).filter_by(id_=dashboard_id).first()


with_dashboard = with_resource_factory('dashboard', dashboard_getter)


def get_dashboards():
    # @jwt_required
    def __func():
        dashboards = current_app.running_context.execution_db.session.query(Dashboard).all()
        r = [dashboard_schema.dump(dashboard) for dashboard in dashboards]

        return jsonify(sorted(r, key=(lambda n: n["name"].lower()))), SUCCESS

    return __func()


def create_dashboard():
    # @jwt_required
    def __func():
        dashboard_name = request.get_json()['name']
        try:
            dashboard = dashboard_schema.load(request.get_json())
            current_app.running_context.execution_db.session.add(dashboard)
            current_app.running_context.execution_db.session.commit()
            return dashboard_schema.dump(dashboard), OBJECT_CREATED
        except ValidationError as e:
            current_app.running_context.execution_db.session.rollback()
            current_app.logger.error('Could not create dashboard {}. Invalid input'.format(dashboard_name))
            return improper_json_problem('dashboard', 'create', dashboard_name, e.messages)
        except (IntegrityError, StatementError):
            current_app.running_context.execution_db.session.rollback()
            current_app.logger.error('Could not create dashboard {}. Unique constraint failed'.format(dashboard_name))
            return unique_constraint_problem('dashboard', 'create', dashboard_name)

    return __func()


def put_dashboard():
    data = request.get_json()
    dashboard_id = data['id_']
    # TODO: figure out why this doesn't work. for some reason it instantly returns 200 and never hits any code inside
    # @jwt_required
    @with_dashboard('read', dashboard_id)
    def __func(dashboard):
        errors = dashboard_schema.load(data, instance=dashboard).errors
        if errors:
            return Problem.from_crud_resource(
                INVALID_INPUT_ERROR,
                'dashboard',
                'update',
                'Could not update dashboard {}. Invalid input.'.format(dashboard_id), ext=errors)
        current_app.logger.error('HALP')
        try:
            current_app.logger.error('HALPtry')
            current_app.running_context.execution_db.session.commit()
        except IntegrityError as e:
            current_app.logger.error('HALPexce')
            current_app.running_context.execution_db.session.rollback()
            current_app.logger.error('Could not update dashboard {}. Unique constraint failed ({})'.format(dashboard_id,
                                                                                                           e))
            return unique_constraint_problem('dashboard', 'update', dashboard_id)

        current_app.logger.error('HALPdone')
        current_app.logger.info('Updated dashboard {0}'.format(dashboard_id))
        return dashboard_schema.dump(dashboard), 400


def get_dashboard(dashboard_id):
    # @jwt_required
    @with_dashboard('read', dashboard_id)
    def __func(dashboard):
        dashboard_json = dashboard_schema.dump(dashboard)
        return jsonify(dashboard_json), SUCCESS

    return __func()


def delete_dashboard(dashboard_id):
    # @jwt_required
    @with_dashboard('delete', dashboard_id)
    def __func(dashboard):
        current_app.running_context.execution_db.session.delete(dashboard)

    return __func()
