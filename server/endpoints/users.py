from flask import request, current_app
from server.security import roles_accepted
from flask_jwt_extended import jwt_required
from server.security import encrypt_password, verify_password
from server.returncodes import *


def read_all_users():
    from server.context import running_context

    @jwt_required
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        result = [user.as_json() for user in running_context.User.query.all()]

        return result, SUCCESS
    return __func()


def create_user():
    from server.context import running_context

    @jwt_required
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        data = request.get_json()
        username = data['username']
        if not running_context.User.query.filter_by(email=username).first():
            password = encrypt_password(data['password'])

            # Creates User
            if 'active' in data:
                user = running_context.user_datastore.create_user(email=username, password=password, active=data['active'])
            else:
                user = running_context.user_datastore.create_user(email=username, password=password)

            if 'roles' in data:
                user.set_roles(data['roles'])

            has_admin = False
            for role in user.roles:
                if role.name == 'admin':
                    has_admin = True
            if not has_admin:
                r = {'name': 'admin', 'description': None}
                user.set_roles([r])

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
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        user = running_context.user_datastore.get_user(id=user_id)
        if user:
            return user.as_json(), SUCCESS
        else:
            current_app.logger.error('Could not display user {0}. User does not exist.'.format(user_id))
            return {"error": 'User with id {0} does not exist.'.format(user_id)}, OBJECT_DNE_ERROR
    return __func()


def update_user():
    from server.context import running_context

    @jwt_required
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        data = request.get_json()
        user = running_context.user_datastore.get_user(id=data['id'])
        if user:
            current_username = user.email

            if 'old_password' in data and 'password' in data:
                if verify_password(data['old_password'], user.password):
                    user.password = encrypt_password(data['password'])
                else:
                    return {"error": "User's current password was entered incorrectly."}, BAD_REQUEST

            if 'active' in data:
                user.active = data['active']
            if 'roles' in data:
                user.set_roles(data['roles'])
            if 'username' in data:
                user.email = data['username']

            running_context.db.session.commit()
            current_app.logger.info('Updated user {0}. Updated to: {1}'.format(current_username, user.as_json()))
            return user.as_json(), SUCCESS
        else:
            current_app.logger.error('Could not edit user {0}. User does not exist.'.format(data['id']))
            return {"error": 'User {0} does not exist.'.format(data['id'])}, OBJECT_DNE_ERROR
    return __func()


def delete_user(user_id):
    from server.flaskserver import running_context, current_user

    @jwt_required
    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        user = running_context.user_datastore.get_user(id=user_id)
        if user:
            if user != current_user:
                running_context.user_datastore.delete_user(user)
                running_context.db.session.commit()
                current_app.logger.info('User {0} deleted'.format(user.email))
                return {}, SUCCESS
            else:
                current_app.logger.error('Could not delete user {0}. User is current user.'.format(user.email))
                return {"error": 'User {0} is current user.'.format(user.email)}, UNAUTHORIZED_ERROR
        else:
            current_app.logger.error('Could not delete user {0}. User does not exist.'.format(user_id))
            return {"error": 'User with id {0} does not exist.'.format(user_id)}, OBJECT_DNE_ERROR
    return __func()
