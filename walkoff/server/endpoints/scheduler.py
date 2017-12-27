from flask import current_app, request
from flask_jwt_extended import jwt_required

from walkoff.core.scheduler import InvalidTriggerArgs
from walkoff.server.returncodes import *
from walkoff.server.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.database.scheduledtasks import ScheduledTask
from walkoff.server.extensions import db


def get_scheduler_status():
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['read']))
    def __func():
        return {"status": running_context.controller.scheduler.scheduler.state}, SUCCESS

    return __func()


def update_scheduler_status(status):
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['update', 'execute']))
    def __func():
        updated_status = running_context.controller.scheduler.scheduler.state
        if status == "start":
            updated_status = running_context.controller.scheduler.start()
            current_app.logger.info('Scheduler started. Status {0}'.format(updated_status))
        elif status == "stop":
            updated_status = running_context.controller.scheduler.stop()
            current_app.logger.info('Scheduler stopped. Status {0}'.format(updated_status))
        elif status == "pause":
            updated_status = running_context.controller.scheduler.pause()
            current_app.logger.info('Scheduler paused. Status {0}'.format(updated_status))
        elif status == "resume":
            updated_status = running_context.controller.scheduler.resume()
            current_app.logger.info('Scheduler resumed. Status {0}'.format(updated_status))
        return {"status": updated_status}, SUCCESS

    return __func()


def read_all_scheduled_tasks():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['read']))
    def __func():
        return [task.as_json() for task in ScheduledTask.query.all()], SUCCESS

    return __func()


def create_scheduled_task():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['create', 'execute']))
    def __func():
        data = request.get_json()
        task = ScheduledTask.query.filter_by(name=data['name']).first()
        if task is None:
            try:
                task = ScheduledTask(**data)
            except InvalidTriggerArgs:
                return {'error': 'invalid scheduler arguments'}, 400
            else:
                db.session.add(task)
                db.session.commit()
                return task.as_json(), OBJECT_CREATED
        else:
            return {'error': 'Could not create object. Object with given name already exists'}, OBJECT_EXISTS_ERROR

    return __func()


def read_scheduled_task(scheduled_task_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['read']))
    def __func():
        task = ScheduledTask.query.filter_by(id=scheduled_task_id).first()
        if task is not None:
            return task.as_json(), SUCCESS
        else:
            return {'error': 'Could not read object. Object does not exist'}, OBJECT_DNE_ERROR

    return __func()


def update_scheduled_task():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['update', 'execute']))
    def __func():
        data = request.get_json()
        task = ScheduledTask.query.filter_by(id=data['id']).first()
        if task is not None:
            if 'name' in data:
                same_name = ScheduledTask.query.filter_by(name=data['name']).first()
                if same_name is not None and same_name.id != data['id']:
                    return {'error': 'Task with that name already exists.'}, OBJECT_EXISTS_ERROR
            try:
                task.update(data)
            except InvalidTriggerArgs:
                return {'error': 'invalid scheduler arguments'}, 400
            else:
                db.session.commit()
                return task.as_json(), SUCCESS
        else:
            return {'error': 'Could not update object. Object does not exist.'}, OBJECT_DNE_ERROR

    return __func()


def delete_scheduled_task(scheduled_task_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['delete']))
    def __func():
        task = ScheduledTask.query.filter_by(id=scheduled_task_id).first()
        if task is not None:
            db.session.delete(task)
            db.session.commit()
            return {}, SUCCESS
        else:
            return {'error': 'Could not delete object. Object does not exist'}, OBJECT_DNE_ERROR

    return __func()


def control_scheduled_task(scheduled_task_id, action):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['execute']))
    def __func():
        task = ScheduledTask.query.filter_by(id=scheduled_task_id).first()
        if task is not None:
            if action == 'start':
                task.start()
                db.session.commit()
                return {}, SUCCESS
            elif action == 'stop':
                task.stop()
                db.session.commit()
                return {}, SUCCESS
        else:
            return {'error': 'Could not read object. Object does not exist'}, OBJECT_DNE_ERROR

    return __func()
