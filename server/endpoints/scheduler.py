import json
from flask import current_app
from flask_security import roles_accepted


def start_scheduler():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        status = running_context.controller.start()
        current_app.logger.info('Scheduler started. Status {0}'.format(status))
        return json.dumps({"status": status})
    return __func()

def stop_scheduler():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        status = running_context.controller.stop()
        current_app.logger.info('Scheduler stopped. Status {0}'.format(status))
        return json.dumps({"status": status})
    return __func()

def pause_scheduler():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        status = running_context.controller.pause()
        current_app.logger.info('Scheduler paused. Status {0}'.format(status))
        return json.dumps({"status": status})
    return __func()

def resume_scheduler():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        status = running_context.controller.resume()
        current_app.logger.info('Scheduler resumed. Status {0}'.format(status))
        return json.dumps({"status": status})
    return __func()

def pause_job(job_id):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        running_context.controller.pause_job(job_id)
        current_app.logger.info('Scheduler paused job {0}'.format(job_id))
        return json.dumps({"status": "Job Paused"})
    return __func()

def resume_job(job_id):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        running_context.controller.resume_job(job_id)
        current_app.logger.info('Scheduler resumed job {0}'.format(job_id))
        return json.dumps({"status": "Job Resumed"})
    return __func()

def get_jobs():
    from server.context import running_context
    #@roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        return running_context.controller.get_scheduled_jobs()
    return __func()
