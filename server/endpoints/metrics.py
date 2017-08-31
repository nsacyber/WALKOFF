from server.security import roles_accepted, jwt_required
import server.metrics as metrics
from server.returncodes import *

@jwt_required
def read_app_metrics():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/metrics'])
    def __func():
        return _convert_action_time_averages(), SUCCESS

    return __func()

@jwt_required
def read_workflow_metrics():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/metrics'])
    def __func():
        return _convert_workflow_time_averages(), SUCCESS

    return __func()


def _convert_action_time_averages():
    apps_json = []
    for app_name, app in metrics.app_metrics.items():
        app_json = {"name": app_name, "count": app['count']}
        actions = []
        for action_name, action in app['actions'].items():
            action_json = {"name": action_name}
            if 'success' in action:
                action_json["success_metrics"] = {"count": action['success']['count'],
                                                  "avg_time": str(action['success']['avg_time'])}
            if 'error' in action:
                action_json["error_metrics"] = {"count": action['error']['count'],
                                                "avg_time": str(action['error']['avg_time'])}
            actions.append(action_json)
        app_json["actions"] = actions
        apps_json.append(app_json)
    return {"apps": apps_json}


def _convert_workflow_time_averages():
    return {"workflows": [{"name": workflow_name,
                           "count": workflow["count"],
                           "avg_time": str(workflow["avg_time"])}
                          for workflow_name, workflow in metrics.workflow_metrics.items()]}
