from flask import request, current_app
from flask_jwt_extended import jwt_required

from walkoff.serverdb import clear_resources_for_role, get_all_available_resource_actions
from walkoff.serverdb.role import Role
from walkoff.extensions import db
from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions, admin_required
from walkoff.server.decorators import with_resource_factory


with_role = with_resource_factory('role', lambda role_id: Role.query.filter_by(id=role_id).first())


def read_all_roles():
    @jwt_required
    @admin_required
    def __func():
        return [role.as_json() for role in Role.query.all()], SUCCESS

    return __func()


def create_role():
    @jwt_required
    @admin_required
    def __func():
        json_data = request.get_json()
        if not Role.query.filter_by(name=json_data['name']).first():
            resources = json_data['resources'] if 'resources' in json_data else []
            if '/roles' in resources:
                resources.remove('/roles')
            role_params = {'name': json_data['name'],
                           'description': json_data['description'] if 'description' in json_data else '',
                           'resources': resources}
            new_role = Role(**role_params)
            db.session.add(new_role)
            db.session.commit()
            current_app.logger.info('Role added: {0}'.format(role_params))
            return new_role.as_json(), OBJECT_CREATED
        else:
            current_app.logger.warning('Cannot add role {0}. Role already exists'.format(json_data['name']))
            return {"error": "Role already exists."}, OBJECT_EXISTS_ERROR

    return __func()


def read_role(role_id):
    @jwt_required
    @admin_required
    @with_role('read', role_id)
    def __func(role):
        return role.as_json(), SUCCESS

    return __func()


def update_role():
    @jwt_required
    @admin_required
    @with_role('update', request.get_json()['id'])
    def __func(role):
        json_data = request.get_json()
        if 'name' in json_data:
            new_name = json_data['name']
            role_db = Role.query.filter_by(name=new_name).first()
            if role_db is None or role_db.id == json_data['id']:
                role.name = new_name
        if 'description' in json_data:
            role.description = json_data['description']
        if 'resources' in json_data:
            resources = json_data['resources']
            role.set_resources(resources)
        db.session.commit()
        current_app.logger.info('Edited role {0} to {1}'.format(json_data['id'], json_data))
        return role.as_json(), SUCCESS

    return __func()


def delete_role(role_id):
    @jwt_required
    @admin_required
    @with_role('delete', role_id)
    def __func(role):
        clear_resources_for_role(role.name)
        db.session.delete(role)
        db.session.commit()
        return {}, NO_CONTENT

    return __func()


def read_available_resource_actions():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('roles', ['read']))
    def __func():
        return get_all_available_resource_actions(), SUCCESS

    return __func()
