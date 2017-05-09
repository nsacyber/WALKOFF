# import json
# from flask import Blueprint, current_app
# from flask_security import auth_token_required, roles_accepted
# from server.flaskserver import running_context
#
# scheduler_page = Blueprint('scheduler_page', __name__)
#
#
# @scheduler_page.route('/<string:action>', methods=['POST'])
# @auth_token_required
# @roles_accepted(*running_context.user_roles['/execution/scheduler'])
# def scheduler_actions(action):
#     if action == 'start':
#         status = running_context.controller.start()
#         current_app.logger.info('Scheduler started. Status {0}'.format(status))
#         return json.dumps({"status": status})
#     elif action == 'stop':
#         status = running_context.controller.stop()
#         current_app.logger.info('Scheduler stopped. Status {0}'.format(status))
#         return json.dumps({"status": status})
#     elif action == 'pause':
#         status = running_context.controller.pause()
#         current_app.logger.info('Scheduler paused. Status {0}'.format(status))
#         return json.dumps({"status": status})
#     elif action == 'resume':
#         status = running_context.controller.resume()
#         current_app.logger.info('Scheduler resumed. Status {0}'.format(status))
#         return json.dumps({"status": status})
#     current_app.logger.error('Scheduler cannot take action {0}. No such action'.format(action))
#     return json.dumps({"status": "invalid command"})
#
#
# @scheduler_page.route('/<string:job_id>/<string:action>', methods=['POST'])
# @auth_token_required
# @roles_accepted(*running_context.user_roles['/execution/scheduler'])
# def scheduler_actions_by_id(job_id, action):
#     if action == "pause":
#         running_context.controller.pause_job(job_id)
#         current_app.logger.info('Scheduler paused job {0}'.format(job_id))
#         return json.dumps({"status": "Job Paused"})
#     elif action == "resume":
#         running_context.controller.resume_job(job_id)
#         current_app.logger.info('Scheduler resumed job {0}'.format(job_id))
#         return json.dumps({"status": "Job Resumed"})
#     current_app.logger.error('Scheduler cannot take action {0} on job {1}. No such action available'.format(action,
#                                                                                                             job_id))
#     return json.dumps({"status": "invalid command"})
#
#
# @scheduler_page.route('/jobs', methods=['GET'])
# @auth_token_required
# # @roles_accepted(*userRoles["/execution/listener"])
# def get_scheduler():
#     return running_context.controller.get_scheduled_jobs()
