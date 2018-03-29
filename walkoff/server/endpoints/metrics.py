from flask_jwt_extended import jwt_required

from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.returncodes import *
from walkoff import executiondb
from walkoff.executiondb.metrics import AppMetric, WorkflowMetric


def read_app_metrics():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('metrics', ['read']))
    def __func():
        return _convert_action_time_averages(), SUCCESS

    return __func()


def read_workflow_metrics():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('metrics', ['read']))
    def __func():
        return _convert_workflow_time_averages(), SUCCESS

    return __func()


def _convert_action_time_averages():
    app_metrics = executiondb.execution_db.session.query(AppMetric).all()
    return {"apps": [app_metric.as_json() for app_metric in app_metrics]}


def _convert_workflow_time_averages():
    workflow_metrics = executiondb.execution_db.session.query(WorkflowMetric).all()
    return {"workflows": [workflow.as_json() for workflow in workflow_metrics]}
