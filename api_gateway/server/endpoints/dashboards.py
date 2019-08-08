from flask import current_app, request, jsonify
from flask_jwt_extended import jwt_required

from marshmallow import ValidationError

from sqlalchemy.exc import IntegrityError, StatementError

from api_gateway import helpers
from api_gateway.server.decorators import with_resource_factory, paginate
from api_gateway.executiondb.dashboard import Dashboard, DashboardSchema
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.problem import unique_constraint_problem, improper_json_problem
from http import HTTPStatus


def dashboard_getter(dashboard):
    if helpers.validate_uuid(dashboard):
        return current_app.running_context.execution_db.session.query(Dashboard).filter_by(id_=dashboard).first()
    else:
        return current_app.running_context.execution_db.session.query(Dashboard).filter_by(name=dashboard).first()


dashboard_schema = DashboardSchema()
with_dashboard = with_resource_factory("dashboard", dashboard_getter)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("dashboards", ["create"]))
def create_dashboard():
    data = request.get_json()
    dashboard_name = data["name"]

    try:
        dashboard = dashboard_schema.load(data)
        current_app.running_context.execution_db.session.add(dashboard)
        current_app.running_context.execution_db.session.commit()
        return dashboard_schema.dump(dashboard), HTTPStatus.CREATED
    except ValidationError as e:
        current_app.running_context.execution_db.session.rollback()
        return improper_json_problem("dashboard", "create", dashboard_name, e.messages)
    except (IntegrityError, StatementError):
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem("dashboard", "create", dashboard_name)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("dashboards", ["read"]))
@paginate(dashboard_schema)
def read_all_dashboards():
    r = current_app.running_context.execution_db.session.query(Dashboard).order_by(Dashboard.name).all()
    return r, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("dashboards", ["update"]))
@with_dashboard("update", "dashboard")
def update_dashboard(dashboard):
    data = request.get_json()
    try:
        dashboard_schema.load(data, instance=dashboard)
        # return invalid_input_problem("dashboard", "update", data["name"], errors)  # ToDo: validation

        current_app.running_context.execution_db.session.commit()
        current_app.logger.info(f"Updated dashboard {dashboard}")
        return dashboard_schema.dump(dashboard), HTTPStatus.OK
    except (IntegrityError, StatementError):
        current_app.running_context.execution_db.session.rollback()
        return unique_constraint_problem("dashboard", "update", data["name"])


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("dashboards", ["read"]))
@with_dashboard("read", "dashboard")
def read_dashboard(dashboard):
    dashboard_json = dashboard_schema.dump(dashboard)
    return jsonify(dashboard_json), HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions("dashboards", ["delete"]))
@with_dashboard("delete", "dashboard")
def delete_dashboard(dashboard):
    current_app.running_context.execution_db.session.delete(dashboard)
    current_app.logger.info(f"Dashboard removed: {dashboard.name}")
    current_app.running_context.execution_db.session.commit()
    return None, HTTPStatus.NO_CONTENT
