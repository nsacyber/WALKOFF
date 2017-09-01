from flask import request, current_app
from server.security import roles_accepted
from flask_jwt_extended import jwt_required
from server.returncodes import *


def read_all_roles():
    from server.context import running_context

    @jwt_required
    @roles_accepted(*running_context.user_roles['/roles'])
    def __func():
        roles = running_context.Role.query.all()
        if roles:
            result = [role.as_json() for role in roles]
            return result, SUCCESS

    return __func()


def create_role():
    from server.context import running_context
    from server.flaskserver import default_urls
    from server.database import add_to_user_roles

    @jwt_required
    @roles_accepted(*running_context.user_roles['/roles'])
    def __func():
        json_data = request.get_json()
        if not running_context.Role.query.filter_by(name=json_data['name']).first():

            role_params = {'name': json_data['name'],
                           'description': json_data['description'] if 'description' in json_data else '',
                           'pages': json_data['pages'] if 'pages' in json_data else default_urls}
            running_context.user_datastore.create_role(**role_params)

            add_to_user_roles(json_data['name'], default_urls)

            running_context.db.session.commit()
            current_app.logger.info('Role added: {0}'.format(role_params))
            return {}, OBJECT_CREATED
        else:
            current_app.logger.warning('Cannot add role {0}. Role already exists'.format(json_data['name']))
            return {"error": "Role already exists."}, OBJECT_EXISTS_ERROR

    return __func()


def read_role(role_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted(*running_context.user_roles['/roles'])
    def __func():
        role = running_context.Role.query.filter_by(name=role_name).first()
        if role:
            return role.display(), SUCCESS
        else:
            current_app.logger.error('Cannot display role {0}. Role does not exist.'.format(role_name))
            return {"error": "Role does not exist."}, OBJECT_DNE_ERROR

    return __func()


def update_role():
    from server.context import running_context
    from server.database import add_to_user_roles

    @jwt_required
    @roles_accepted(*running_context.user_roles['/roles'])
    def __func():
        json_data = request.get_json()
        role = running_context.Role.query.filter_by(name=json_data['name']).first()
        if role:
            if 'description' in json_data:
                role.set_description(json_data['description'])
            if 'pages' in json_data:
                add_to_user_roles(json_data['name'], json_data['pages'])
            current_app.logger.info('Edited role {0} to {1}'.format(json_data['name'], json_data))
            return role.display(), SUCCESS
        else:
            current_app.logger.error('Cannot edit role. Role does not exist.')
            return {"error": "Role does not exist."}, OBJECT_DNE_ERROR

    return __func()
