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
with_username = with_resource_factory('user', lambda username: User.query.filter_by(username=username).first())
import logging
logger = logging.getLogger(__name__)


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('users', ['read']))
def read_all_users():
    page = request.args.get('page', 1, type=int)
    users = []
    for user in User.query.paginate(page, current_app.config['ITEMS_PER_PAGE'], False).items:
        # check for internal user
        if user.id != 1:
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
    # check for internal user
    if user_id.id == 1:
        return None, HTTPStatus.FORBIDDEN
    else:
        return user_id.as_json(), HTTPStatus.OK


@jwt_required
@with_username('read', 'username')
def read_personal_user(username):
    current_id = get_jwt_identity()
    if current_id == username.id:
        return username.as_json(), HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@jwt_required
def list_permissions():
    current_id = get_jwt_identity()
    current_user = User.query.filter_by(id=current_id).first()
    return current_user.permission_json(), HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('users', ['update']))
@with_user('update', 'user_id')
def update_user(user_id):
    data = request.get_json()
    current_user = get_jwt_identity()

    # check for internal user
    if user_id.id == 1:
        return None, HTTPStatus.FORBIDDEN

    if user_id.id == current_user:
        # check for super_admin, allows ability to update username/password but not roles/active
        if user_id.id == 2:
            user_id.set_roles([2])
            user_id.active = True
            return update_user_fields(data, user_id)
        return role_update_user_fields(data, user_id, update=True)
    else:
        # check for super_admin
        if user_id.id == 2:
            return None, HTTPStatus.FORBIDDEN
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


@jwt_required
@with_username('read', 'username')
def update_personal_user(username):
    data = request.get_json()
    current_user = get_jwt_identity()

    # check for internal user
    if username.id == 1:
        return Problem.from_crud_resource(
            HTTPStatus.FORBIDDEN,
            'user',
            'update',
            f"Current user does not have permission to update user {username.id}.")

    if username.id == current_user:
        # allow ability to update username/password but not roles/active
        if username.id == 2:
            username.set_roles([2])
            username.active = True
            return update_user_fields(data, username)
        else:
            return update_user_fields(data, username)
    else:
        return Problem.from_crud_resource(
            HTTPStatus.FORBIDDEN,
            'user',
            'update',
            f"Current user does not have permission to update user {username.id}.")


@permissions_accepted_for_resources(ResourcePermissions('users', ['update']))
def role_update_user_fields(data, user, update=False):
    # ensures inability to update roles for super_admin
    if 'roles' in data and user.id != 2:
        user.set_roles([role['id'] for role in data['roles']])
    if 'active' in data and user.id != 2:
        user.active = data['active']
    if update:
        return update_user_fields(data, user)


def update_user_fields(data, user):
    if user.id != 1:
        original_username = str(user.username)
        if 'username' in data and data['username']:
            user_db = User.query.filter_by(username=data['username']).first()
            if user_db is None or user_db.id == user.id:
                user.username = data['username']
            else:
                return Problem(HTTPStatus.BAD_REQUEST, 'Cannot update user.',
                               f"Username {data['username']} is already taken.")
        elif 'new_username' in data and data['new_username']:
            user_db = User.query.filter_by(username=data['old_username']).first()
            if user_db is None or user_db.id == user.id:
                user.username = data['new_username']
            else:
                return Problem(HTTPStatus.BAD_REQUEST, 'Cannot update user.',
                               f"Username {data['new_username']} is already taken.")
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
    else:
        return None, HTTPStatus.FORBIDDEN


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('users', ['delete']))
@with_user('delete', 'user_id')
def delete_user(user_id):
    if user_id.id != get_jwt_identity() and user_id.id != 1 and user_id.id != 2:
        db.session.delete(user_id)
        db.session.commit()
        current_app.logger.info(f"User {user_id.username} deleted")
        return None, HTTPStatus.NO_CONTENT
    else:
        if user_id.id == get_jwt_identity():
            current_app.logger.error(f"Could not delete user {user_id.id}. User is current user.")
            return Problem.from_crud_resource(HTTPStatus.FORBIDDEN, 'user', 'delete',
                                              'Current user cannot delete self.')
        if user_id.id == 2:
            current_app.logger.error(f"Could not delete user {user_id.username}. "
                                     f"You do not have permission to delete Super Admin.")
            return Problem.from_crud_resource(HTTPStatus.FORBIDDEN, 'user', 'delete',
                                              'A user cannot delete Super Admin.')
        if user_id.id == 1:
            current_app.logger.error(f"Could not delete user {user_id.username}. "
                                     f"You do not have permission to delete WALKOFF's internal user.")
            return Problem.from_crud_resource(HTTPStatus.FORBIDDEN, 'user', 'delete',
                                              "A user cannot delete WALKOFF's internal user.")
