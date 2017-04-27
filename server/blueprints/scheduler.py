import json
from flask import Blueprint
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context

scheduler_page = Blueprint('scheduler_page', __name__)


@scheduler_page.route('/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/scheduler'])
def scheduler_actions(action):
    if action == 'start':
        status = running_context.controller.start()
        return json.dumps({"status": status})
    elif action == 'stop':
        status = running_context.controller.stop()
        return json.dumps({"status": status})
    elif action == 'pause':
        status = running_context.controller.pause()
        return json.dumps({"status": status})
    elif action == 'resume':
        status = running_context.controller.resume()
        return json.dumps({"status": status})
    return json.dumps({"status": "invalid command"})


@scheduler_page.route('/<string:job_id>/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/scheduler'])
def scheduler_actions_by_id(job_id, action):
    if action == "pause":
        running_context.controller.pause_job(job_id)
        return json.dumps({"status": "Job Paused"})
    elif action == "resume":
        running_context.controller.resume_job(job_id)
        return json.dumps({"status": "Job Resumed"})
    return json.dumps({"status": "invalid command"})


@scheduler_page.route('/jobs', methods=['GET'])
@auth_token_required
# @roles_accepted(*userRoles["/execution/listener"])
def scheduler():
    return running_context.controller.get_scheduled_jobs()


#TODO: DELETE
@scheduler_page.route('/jobs', methods=['POST'])
@auth_token_required
# @roles_accepted(*userRoles["/execution/listener"])
def scheduler():
    return running_context.controller.get_scheduled_jobs()
