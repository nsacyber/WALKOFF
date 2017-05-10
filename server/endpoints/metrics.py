from flask_security import roles_accepted
import server.metrics as metrics
from copy import deepcopy


def get_app_metrics():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/metrics'])
    def __func():
        return _convert_action_time_averages()
    return __func()

def get_workflow_metrics():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/metrics'])
    def __func():
        return _convert_workflow_time_averages()
    return __func()

def _convert_action_time_averages():
    ret = deepcopy(metrics.app_metrics)
    for app_name, app in ret.items():
        for action_name, action in app['actions'].items():
            if 'success' in action:
                action['success']['avg_time'] = str(action['success']['avg_time'])
            if 'error' in action:
                action['error']['avg_time'] = str(action['error']['avg_time'])
    return ret

def _convert_workflow_time_averages():
    ret = deepcopy(metrics.workflow_metrics)
    for workflow in ret.values():
        workflow['avg_time'] = str(workflow['avg_time'])
    return ret
