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


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('users', ['read']))
def read_all_users():
    page = request.args.get('page', 1, type=int)
    users = []
    for user in User.query.paginate(page, current_app.config['ITEMS_PER_PAGE'], False).items:
        if user.username != "internal_user":
            users.append(user.as_json())
    return users, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('users', ['create']))
def create_user():
    data = request.get_json()
    username = data['username']
    if not User.query.filter_by(username=username).first():
        user = add_user(username=username, password=data['password'])

        if 'roles' in data or 'active' in data:
            role_update_user_fields(data, user)

        db.session.commit()
        current_app.logger.info(f'User added: {user.as_json()}')
        return user.as_json(), HTTPStatus.CREATED
    else:
        current_app.logger.warning(f'Cannot create user {username}. User already exists.')
        return Problem.from_crud_resource(
            HTTPStatus.BAD_REQUEST,
            'user',
            'create',
            f'User with username {username} already exists')


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('users', ['read']))
@with_user('read', 'user_id')
def read_user(user_id):
    user = User.query.filter_by(User.id == user_id).first()
    if user.username != "internal_user":
        return user_id.as_json(), HTTPStatus.OK
    return None, HTTPStatus.FORBIDDEN


@jwt_required
@with_user('update', 'user_id')
def update_user(user_id):
    data = request.get_json()
    current_user = get_jwt_identity()
    if user_id.id == current_user:
        return update_user_fields(data, user_id)
    else:
        response = role_update_user_fields(data, user_id, update=True)
        if isinstance(response, tuple) and response[1] == HTTPStatus.FORBIDDEN:
            current_app.logger.error(f"User {current_user} does not have permission to update user {user_id.id}")
            return Problem.from_crud_resource(
                HTTPStatus.FORBIDDEN,
                'user',
                'update',
                f"Current user does not have permission to update user {user_id.id}.")
        else:
            return response


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
                           f"Username {data['username']} is already taken.")
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
    current_app.logger.info(f"Updated user {user.id}. Updated to: {user.as_json()}")
    return user.as_json(), HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('users', ['delete']))
@with_user('delete', 'user_id')
def delete_user(user_id):
    if user_id.id != get_jwt_identity():
        db.session.delete(user_id)
        db.session.commit()
        current_app.logger.info(f"User {user_id.username} deleted")
        return None, HTTPStatus.NO_CONTENT
    else:
        current_app.logger.error(f"Could not delete user {user_id.id}. User is current user.")
        return Problem.from_crud_resource(HTTPStatus.FORBIDDEN, 'user', 'delete',
                                          'Current user cannot delete self.')

