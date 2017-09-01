from flask import current_app
from server.security import roles_accepted
from flask_jwt_extended import jwt_required
from server.returncodes import *


@jwt_required
def get_scheduler_status():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        return {"status": running_context.controller.scheduler.state}, SUCCESS

    return __func()


@jwt_required
def update_scheduler_status(status):
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        updated_status = running_context.controller.scheduler.state
        if status == "start":
            updated_status = running_context.controller.start()
            current_app.logger.info('Scheduler started. Status {0}'.format(updated_status))
        elif status == "stop":
            updated_status = running_context.controller.stop()
            current_app.logger.info('Scheduler stopped. Status {0}'.format(updated_status))
        elif status == "pause":
            updated_status = running_context.controller.pause()
            current_app.logger.info('Scheduler paused. Status {0}'.format(updated_status))
        elif status == "resume":
            updated_status = running_context.controller.resume()
            current_app.logger.info('Scheduler resumed. Status {0}'.format(updated_status))
        return {"status": updated_status}, SUCCESS

    return __func()


@jwt_required
def update_job_status(job_id, status):
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        updated_status = "No update"
        if status == "pause":
            running_context.controller.pause_job(job_id)
            current_app.logger.info('Scheduler paused job {0}'.format(job_id))
            updated_status = "Job Paused"
        elif status == "resume":
            running_context.controller.resume_job(job_id)
            current_app.logger.info('Scheduler resumed job {0}'.format(job_id))
            updated_status = "Job Resumed"
        return {"status": updated_status}, SUCCESS

    return __func()


def read_all_jobs():
    from server.context import running_context

    # @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        jobs = []
        for job in running_context.controller.get_scheduled_jobs():
            jobs.append({"name": job.name, "id": job.id})
        return {"jobs": jobs}, SUCCESS

    return __func()
