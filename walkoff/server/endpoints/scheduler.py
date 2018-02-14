from flask import current_app, request
from flask_jwt_extended import jwt_required

from walkoff.core.scheduler import InvalidTriggerArgs
from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.serverdb.scheduledtasks import ScheduledTask
from walkoff.extensions import db
from walkoff.server.decorators import with_resource_factory
from uuid import UUID


with_task = with_resource_factory('Scheduled task', lambda task_id: ScheduledTask.query.filter_by(id=task_id).first())


def validate_uuids(uuids):
    invalid_uuids = []
    for uuid in uuids:
        try:
            UUID(uuid)
        except ValueError:
            invalid_uuids.append(uuid)
    return invalid_uuids


def get_scheduler_status():
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['read']))
    def __func():
        return {"status": running_context.scheduler.scheduler.state}, SUCCESS

    return __func()


def update_scheduler_status():
    from walkoff.server.context import running_context

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['update', 'execute']))
    def __func():
        status = request.get_json()['status']
        updated_status = running_context.scheduler.scheduler.state
        if status == "start":
            updated_status = running_context.scheduler.start()
            current_app.logger.info('Scheduler started. Status {0}'.format(updated_status))
        elif status == "stop":
            updated_status = running_context.scheduler.stop()
            current_app.logger.info('Scheduler stopped. Status {0}'.format(updated_status))
        elif status == "pause":
            updated_status = running_context.scheduler.pause()
            current_app.logger.info('Scheduler paused. Status {0}'.format(updated_status))
        elif status == "resume":
            updated_status = running_context.scheduler.resume()
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
        invalid_uuids = validate_uuids(data['workflows'])
        if invalid_uuids:
            return {'error': 'Invalid UUIDs {}'.format(invalid_uuids)}, 400
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
    @with_task('read', scheduled_task_id)
    def __func(task):
        return task.as_json(), SUCCESS

    return __func()


def update_scheduled_task():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['update', 'execute']))
    @with_task('update', request.get_json()['id'])
    def __func(task):
        data = request.get_json()
        invalid_uuids = validate_uuids(data.get('workflows', []))
        if invalid_uuids:
            return {'error': 'Invalid UUIDs {}'.format(invalid_uuids)}, 400
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

    return __func()


def delete_scheduled_task(scheduled_task_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['delete']))
    @with_task('delete', scheduled_task_id)
    def __func(task):
        db.session.delete(task)
        db.session.commit()
        return {}, NO_CONTENT

    return __func()


def control_scheduled_task():
    scheduled_task_id = request.get_json()['id']

    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('scheduler', ['execute']))
    @with_task('control', scheduled_task_id)
    def __func(task):
        action = request.get_json()['action']
        if action == 'start':
            task.start()
        elif action == 'stop':
            task.stop()
        db.session.commit()
        return {}, SUCCESS

    return __func()
