from flask import request, current_app
from flask_jwt_extended import jwt_required

from server.database import set_resources_for_role, clear_resources_for_role
from server.returncodes import *
from server.security import roles_accepted


def read_all_roles():
    from server.context import running_context

    @jwt_required
    @roles_accepted('admin')
    def __func():
        return [role.as_json() for role in running_context.Role.query.all()], SUCCESS

    return __func()


def create_role():
    from server.context import running_context

    @jwt_required
    @roles_accepted('admin')
    def __func():
        json_data = request.get_json()
        if not running_context.Role.query.filter_by(name=json_data['name']).first():
            resources = json_data['resources'] if 'resources' in json_data else []
            if '/roles' in resources:
                resources.remove('/roles')
            role_params = {'name': json_data['name'],
                           'description': json_data['description'] if 'description' in json_data else '',
                           'resources': resources}
            new_role = running_context.Role(**role_params)
            running_context.db.session.add(new_role)
            running_context.db.session.commit()
            set_resources_for_role(json_data['name'], resources)
            current_app.logger.info('Role added: {0}'.format(role_params))
            return new_role.as_json(), OBJECT_CREATED
        else:
            current_app.logger.warning('Cannot add role {0}. Role already exists'.format(json_data['name']))
            return {"error": "Role already exists."}, OBJECT_EXISTS_ERROR

    return __func()


def read_role(role_id):
    from server.context import running_context

    @jwt_required
    @roles_accepted('admin')
    def __func():
        role = running_context.Role.query.filter_by(id=role_id).first()
        if role:
            return role.as_json(), SUCCESS
        else:
            current_app.logger.error('Cannot display role {0}. Role does not exist.'.format(role_id))
            return {"error": "Role does not exist."}, OBJECT_DNE_ERROR

    return __func()


def update_role():
    from server.context import running_context

    @jwt_required
    @roles_accepted('admin')
    def __func():
        json_data = request.get_json()
        role = running_context.Role.query.filter_by(id=json_data['id']).first()
        if role is not None:
            if 'name' in json_data:
                new_name = json_data['name']
                role_db = running_context.Role.query.filter_by(name=new_name).first()
                if role_db is None or role_db.id == json_data['id']:
                    role.name = new_name
            if 'description' in json_data:
                role.description = json_data['description']
            if 'resources' in json_data:
                resources = json_data['resources']
                if '/roles' in resources:
                    resources.remove('/roles')
                role.set_resources(resources)
                set_resources_for_role(role.name, resources)
            running_context.db.session.commit()
            current_app.logger.info('Edited role {0} to {1}'.format(json_data['id'], json_data))
            return role.as_json(), SUCCESS
        else:
            current_app.logger.error('Cannot edit role. Role does not exist.')
            return {"error": "Role does not exist."}, OBJECT_DNE_ERROR

    return __func()


def delete_role(role_id):
    from server.context import running_context

    @jwt_required
    @roles_accepted('admin')
    def __func():
        role = running_context.Role.query.filter_by(id=role_id).first()
        if role:
            clear_resources_for_role(role.name)
            running_context.db.session.delete(role)
            return {}, SUCCESS
        else:
            current_app.logger.error('Cannot delete role {0}. Role does not exist.'.format(role_id))
            return {"error": "Role does not exist."}, OBJECT_DNE_ERROR

    return __func()
