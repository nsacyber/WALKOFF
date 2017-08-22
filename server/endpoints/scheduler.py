from flask import current_app, request
from flask_security import roles_accepted
from server.returncodes import *


def get_scheduler_status():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/scheduler'])
    def __func():
        return {"status": running_context.controller.scheduler.state}, SUCCESS
    return __func()


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


def read_all_scheduled_tasks():
    from server.context import running_context

    def __func():
        return [task.as_json() for task in running_context.ScheduledTask.query.all()], SUCCESS
    return __func()


def create_scheduled_task():
    from server.context import running_context

    def __func():
        data = request.get_json()
        task = running_context.ScheduledTask.query.filter_by(name=data['name']).first()
        if task is None:
            task = running_context.ScheduledTask(**data)
            running_context.db.session.add(task)
            running_context.db.session.commit()
            return task.as_json(), OBJECT_CREATED
        else:
            return {'error': 'Could not create object. Object with given name already exists'}, OBJECT_EXISTS_ERROR
    return __func()


def read_scheduled_task(scheduled_task_id):
    from server.context import running_context

    def __func():
        task = running_context.ScheduledTask.query.filter_by(id=scheduled_task_id).first()
        if task is not None:
            return task.as_json(), SUCCESS
        else:
            return {'error': 'Could not read object. Object does not exist'}, OBJECT_DNE_ERROR

    return __func()


def update_scheduled_task():
    from server.context import running_context

    def __func():
        data = request.get_json()
        task = running_context.ScheduledTask.query.filter_by(id=data['id']).first()
        if task is not None:
            if 'name' in data and running_context.ScheduledTask.query.filter_by(name=data['name']).first() is not None:
                return {'error': 'Task with that name already exists.'}, OBJECT_EXISTS_ERROR
            task.update(data)
            running_context.db.session.commit()
            return task.as_json(), SUCCESS
        else:
            return {'error': 'Could not read object. Object does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def delete_scheduled_task(scheduled_task_id):
    from server.context import running_context

    def __func():
        task = running_context.ScheduledTask.query.filter_by(id=scheduled_task_id).first()
        if task is not None:
            running_context.db.session.delete(task)
            running_context.db.session.commit()
            return {}, SUCCESS
        else:
            return {'error': 'Could not read object. Object does not exist'}, OBJECT_DNE_ERROR

    return __func()


def enable_scheduled_task(scheduled_task_id):
    from server.context import running_context

    def __func():
        task = running_context.ScheduledTask.query.filter_by(id=scheduled_task_id).first()
        if task is not None:
            task.enable()
            running_context.db.session.commit()
            return {}, SUCCESS
        else:
            return {'error': 'Could not read object. Object does not exist'}, OBJECT_DNE_ERROR

    return __func()


def disable_scheduled_task(scheduled_task_id):
    from server.context import running_context

    def __func():
        task = running_context.ScheduledTask.query.filter_by(id=scheduled_task_id).first()
        if task is not None:
            task.disable()
            running_context.db.session.commit()
            return {}, SUCCESS
        else:
            return {'error': 'Could not read object. Object does not exist'}, OBJECT_DNE_ERROR

    return __func()