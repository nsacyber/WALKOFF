from flask import request, current_app
from server.security import roles_accepted
from flask_jwt_extended import jwt_required
from server.returncodes import *


def read_all_users():
    from server.context import running_context

    @jwt_required
    @roles_accepted(*running_context.resource_roles['/users'])
    def __func():
        return [user.as_json() for user in running_context.User.query.all()], SUCCESS
    return __func()


def create_user():
    from server.context import running_context
    from server.database import add_user

    @jwt_required
    @roles_accepted(*running_context.resource_roles['/users'])
    def __func():
        data = request.get_json()
        username = data['username']
        if not running_context.User.query.filter_by(username=username).first():
            user = add_user(username=username, password=data['password'])
            if 'roles' in data:
                user.set_roles(data['roles'])

            running_context.db.session.commit()
            current_app.logger.info('User added: {0}'.format(user.as_json()))
            return user.as_json(), OBJECT_CREATED
        else:
            current_app.logger.warning('Could not create user {0}. User already exists.'.format(username))
            return {"error": "User {0} already exists.".format(username)}, OBJECT_EXISTS_ERROR
    return __func()


def read_user(user_id):
    from server.context import running_context

    @jwt_required
    @roles_accepted(*running_context.resource_roles['/users'])
    def __func():
        user = running_context.User.query.filter_by(id=user_id).first()
        if user:
            return user.as_json(), SUCCESS
        else:
            current_app.logger.error('Could not display user {0}. User does not exist.'.format(user_id))
            return {"error": 'User with id {0} does not exist.'.format(user_id)}, OBJECT_DNE_ERROR
    return __func()


def update_user():
    from server.context import running_context

    @jwt_required
    @roles_accepted(*running_context.resource_roles['/users'])
    def __func():
        data = request.get_json()
        user = running_context.User.query.filter_by(id=data['id']).first()
        if user is not None:
            original_username = str(user.username)
            if 'username' in data and data['username']:
                user_db = running_context.User.query.filter_by(username=data['username']).first()
                if user_db is None or user_db.id == user.id:
                    user.username = data['username']
                else:
                    return {"error": "Username is taken"}, BAD_REQUEST
            if 'old_password' in data and 'password' in data:
                if user.verify_password(data['old_password']):
                    user.password = data['password']
                else:
                    user.username = original_username
                    return {"error": "User's current password was entered incorrectly."}, BAD_REQUEST
            if 'roles' in data:
                user.set_roles(data['roles'])

            running_context.db.session.commit()
            current_app.logger.info('Updated user {0}. Updated to: {1}'.format(user.id, user.as_json()))
            return user.as_json(), SUCCESS
        else:
            current_app.logger.error('Could not edit user {0}. User does not exist.'.format(data['id']))
            return {"error": 'User {0} does not exist.'.format(data['id'])}, OBJECT_DNE_ERROR
    return __func()


def delete_user(user_id):
    from server.flaskserver import running_context, current_user

    @jwt_required
    @roles_accepted(*running_context.resource_roles['/users'])
    def __func():
        user = running_context.User.query.filter_by(id=user_id).first()
        if user:
            if user != current_user:
                running_context.db.session.delete(user)
                running_context.db.session.commit()
                current_app.logger.info('User {0} deleted'.format(user.username))
                return {}, SUCCESS
            else:
                current_app.logger.error('Could not delete user {0}. User is current user.'.format(user.id))
                return {"error": 'User {0} is current user.'.format(user.username)}, UNAUTHORIZED_ERROR
        else:
            current_app.logger.error('Could not delete user {0}. User does not exist.'.format(user_id))
            return {"error": 'User with id {0} does not exist.'.format(user_id)}, OBJECT_DNE_ERROR
    return __func()
