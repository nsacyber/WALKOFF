# from flask import Blueprint
# from flask_security import auth_token_required, roles_accepted
# import server.metrics as metrics
# from server.flaskserver import running_context
# import json
# from copy import deepcopy
#
# metrics_page = Blueprint('metrics_page', __name__)
#
#
# def _convert_action_time_averages():
#     ret = deepcopy(metrics.app_metrics)
#     for app_name, app in ret.items():
#         for action_name, action in app['actions'].items():
#             if 'success' in action:
#                 action['success']['avg_time'] = str(action['success']['avg_time'])
#             if 'error' in action:
#                 action['error']['avg_time'] = str(action['error']['avg_time'])
#     return ret
#
#
# @metrics_page.route('/apps', methods=['GET'])
# @auth_token_required
# @roles_accepted(*running_context.user_roles['/metrics'])
# def get_app_metrics():
#     return json.dumps(_convert_action_time_averages())
#
#
# def _convert_workflow_time_averages():
#     ret = deepcopy(metrics.workflow_metrics)
#     for workflow in ret.values():
#         workflow['avg_time'] = str(workflow['avg_time'])
#     return ret
#
#
# @metrics_page.route('/workflows', methods=['GET'])
# @auth_token_required
# @roles_accepted(*running_context.user_roles['/metrics'])
# def get_workflow_metrics():
#     return json.dumps(_convert_workflow_time_averages())
