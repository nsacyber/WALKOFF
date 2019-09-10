from flask import request, current_app
from flask_jwt_extended import jwt_required

from api_gateway.extensions import db
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory
from api_gateway.server.problem import Problem
from http import HTTPStatus
from api_gateway.serverdb import clear_resources_for_role, get_all_available_resource_actions
from api_gateway.serverdb.role import Role

with_role = with_resource_factory('role', lambda role_id: Role.query.filter_by(id=role_id).first())


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('roles', ['read']))
def read_all_roles():
    roles = []
    for role in Role.query.all():
        # hides internal and super_admin roles
        if role.id != 1 and role.id != 2:
            roles.append(role.as_json())
    return roles, HTTPStatus.OK


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('roles', ['create']))
def create_role():
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
        current_app.logger.info(f"Role added: {role_params}")
        return new_role.as_json(), HTTPStatus.CREATED
    else:
        current_app.logger.warning(f"Role with name {json_data['name']} already exists")
        return Problem.from_crud_resource(
            HTTPStatus.BAD_REQUEST,
            'role',
            'create',
            f"Role with name {json_data['name']} already exists")


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('roles', ['read']))
@with_role('read', 'role_id')
def read_role(role_id):
    # check for internal or super_admin
    if role_id.id != 1 or role_id.id != 2:
        return role_id.as_json(), HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('roles', ['update']))
@with_role('update', 'role_id')
def update_role(role_id):
    if role_id.id != 1 and role_id.id != 2:
        json_data = request.get_json()
        if 'name' in json_data:
            new_name = json_data['name']
            role_db = Role.query.filter_by(name=new_name).first()
            if role_db is None or role_db.id == json_data['id']:
                role_id.name = new_name
        if 'description' in json_data:
            role_id.description = json_data['description']
        if 'resources' in json_data:
            resources = json_data['resources']
            role_id.set_resources(resources)
        db.session.commit()
        current_app.logger.info(f"Edited role {json_data['id']} to {json_data}")
        return role_id.as_json(), HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('roles', ['delete']))
@with_role('delete', 'role_id')
def delete_role(role_id):
    if role_id.id != 1 or role_id.id != 2:
        clear_resources_for_role(role_id.name)
        db.session.delete(role_id)
        db.session.commit()
        return None, HTTPStatus.NO_CONTENT
    else:
        return None, HTTPStatus.FORBIDDEN


@jwt_required
@permissions_accepted_for_resources(ResourcePermissions('roles', ['read']))
def read_available_resource_actions():
    return get_all_available_resource_actions(), HTTPStatus.OK

