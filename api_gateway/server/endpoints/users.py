from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from api_gateway.extensions import db
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions, admin_required
from api_gateway.server.decorators import with_resource_factory
from api_gateway.server.problem import Problem
from http import HTTPStatus
from api_gateway.serverdb import add_user
from api_gateway.serverdb.user import User

with_user = with_resource_factory('user', lambda user_id: User.query.filter_by(id=user_id).first())


def read_all_users():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('users', ['read']))
    def __func():
        page = request.args.get('page', 1, type=int)
        return [user.as_json() for user in
                User.query.paginate(page, current_app.config['ITEMS_PER_PAGE'], False).items], HTTPStatus.OK

    return __func()


def create_user():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('users', ['create']))
    def __func():
        data = request.get_json()
        username = data['username']
        if not User.query.filter_by(username=username).first():
            user = add_user(username=username, password=data['password'])

            if 'roles' in data or 'active' in data:
                role_update_user_fields(data, user)

            db.session.commit()
            current_app.logger.info('User added: {0}'.format(user.as_json()))
            return user.as_json(), HTTPStatus.CREATED
        else:
            current_app.logger.warning('Cannot create user {0}. User already exists.'.format(username))
            return Problem.from_crud_resource(
                HTTPStatus.BAD_REQUEST,
                'user',
                'create',
                'User with username {} already exists'.format(username))

    return __func()


def read_user(user_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('users', ['read']))
    @with_user('read', user_id)
    def __func(user):
        return user.as_json(), HTTPStatus.OK

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
            response = role_update_user_fields(data, user, update=True)
            if isinstance(response, tuple) and response[1] == HTTPStatus.FORBIDDEN:
                current_app.logger.error('User {0} does not have permission to '
                                         'update user {1}'.format(current_user, user.id))
                return Problem.from_crud_resource(
                    HTTPStatus.FORBIDDEN,
                    'user',
                    'update',
                    'Current user does not have permission to update user {}.'.format(user_id))
            else:
                return response

    return __func()


def patch_user():
    return update_user()


@admin_required
def role_update_user_fields(data, user, update=False):
    if 'roles' in data:
        user.set_roles([role['id'] for role in data['roles']])
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
            return Problem(HTTPStatus.BAD_REQUEST, 'Cannot update user.',
                           'Username {} is already taken.'.format(data['username']))
    if 'old_password' in data and 'password' in data:
        if user.verify_password(data['old_password']):
            user.password = data['password']
        else:
            user.username = original_username
            return Problem.from_crud_resource(
                HTTPStatus.UNAUTHORIZED,
                'user',
                'update',
                'Current password is incorrect.')
    db.session.commit()
    current_app.logger.info('Updated user {0}. Updated to: {1}'.format(user.id, user.as_json()))
    return user.as_json(), HTTPStatus.OK


def delete_user(user_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('users', ['delete']))
    @with_user('delete', user_id)
    def __func(user):
        if user.id != get_jwt_identity():
            db.session.delete(user)
            db.session.commit()
            current_app.logger.info('User {0} deleted'.format(user.username))
            return None, HTTPStatus.NO_CONTENT
        else:
            current_app.logger.error('Could not delete user {0}. User is current user.'.format(user.id))
            return Problem.from_crud_resource(HTTPStatus.FORBIDDEN, 'user', 'delete',
                                              'Current user cannot delete self.')

    return __func()
