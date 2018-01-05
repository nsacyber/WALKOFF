from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from walkoff.server.returncodes import *
from walkoff.database import add_user
from walkoff.server.extensions import db
from walkoff.database.user import User
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions, admin_required
from walkoff.server.decorators import with_resource_factory


with_user = with_resource_factory('user', lambda user_id: User.query.filter_by(id=user_id).first())


def read_all_users():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('users', ['read']))
    def __func():
        return [user.as_json() for user in User.query.all()], SUCCESS

    return __func()


def create_user():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('users', ['create']))
    def __func():
        data = request.get_json()
        username = data['username']
        if not User.query.filter_by(username=username).first():
            user = add_user(username=username, password=data['password'])

            if 'role_ids' in data or 'active' in data:
                role_update_user_fields(data, user)

            db.session.commit()
            current_app.logger.info('User added: {0}'.format(user.as_json()))
            return user.as_json(), OBJECT_CREATED
        else:
            current_app.logger.warning('Could not create user {0}. User already exists.'.format(username))
            return {"error": "User {0} already exists.".format(username)}, OBJECT_EXISTS_ERROR

    return __func()


def read_user(user_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('users', ['read']))
    @with_user('read', user_id)
    def __func(user):
        return user.as_json(), SUCCESS

    return __func()


def update_user():

    user_id = request.get_json()['id']

    @jwt_required
    @with_user('update', user_id)
    def __func(user):
        data = request.get_json()
        current_user = get_jwt_identity()
        if user.id == current_user:
            return update_user_fields(data, user)
        else:
            message, return_code = role_update_user_fields(data, user, update=True)
            if return_code == FORBIDDEN_ERROR:
                current_app.logger.error('User {0} does not have permission to '
                                         'update user {1}'.format(current_user, user.id))
                return {"error": 'Insufficient Permissions'}, FORBIDDEN_ERROR
            else:
                return message, return_code

    return __func()


@admin_required
def role_update_user_fields(data, user, update=False):
    if 'role_ids' in data:
        user.set_roles(data['role_ids'])
    if 'active' in data:
        user.active = data['active']
    if update:
        return update_user_fields(data, user)


def update_user_fields(data, user):
    original_username = str(user.username)
    if 'username' in data and data['username']:
        user_db = User.query.filter_by(username=data['username']).first()
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
    db.session.commit()
    current_app.logger.info('Updated user {0}. Updated to: {1}'.format(user.id, user.as_json()))
    return user.as_json(), SUCCESS


def delete_user(user_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('users', ['delete']))
    @with_user('delete', user_id)
    def __func(user):
        if user.id != get_jwt_identity():
            db.session.delete(user)
            db.session.commit()
            current_app.logger.info('User {0} deleted'.format(user.username))
            return {}, SUCCESS
        else:
            current_app.logger.error('Could not delete user {0}. User is current user.'.format(user.id))
            return {"error": 'User {0} is current user.'.format(user.username)}, FORBIDDEN_ERROR

    return __func()
