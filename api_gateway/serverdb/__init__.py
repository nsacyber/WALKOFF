import logging

from api_gateway.extensions import db
from api_gateway.serverdb.resource import Resource, Permission
from api_gateway.serverdb.role import Role
from api_gateway.serverdb.user import User

logger = logging.getLogger(__name__)

default_resource_permissions_admin = [{"name": "app_apis", "permissions": ["read"]},
                                      {"name": "configuration", "permissions": ["read", "update"]},
                                      {"name": "global_variables",
                                       "permissions": ["create", "read", "update", "delete"]},
                                      {"name": "workflow_variables",
                                       "permissions": ["create", "read", "update", "delete"]},
                                      {"name": "workflows",
                                       "permissions": ["create", "read", "update", "delete", "execute"]},
                                      {"name": "roles", "permissions": ["create", "read", "update", "delete"]},
                                      {"name": "scheduler",
                                       "permissions": ["create", "read", "update", "delete", "execute"]},
                                      {"name": "users", "permissions": ["create", "read", "update", "delete"]}]

default_resource_permissions_guest = [{"name": "app_apis", "permissions": ["read"]},
                                      {"name": "configuration", "permissions": ["read"]},
                                      {"name": "global_variables", "permissions": ["read", "update"]},
                                      {"name": "workflow_variables", "permissions": ["read", "update"]},
                                      {"name": "workflows", "permissions": ["read"]},
                                      {"name": "roles", "permissions": ["read"]},
                                      {"name": "scheduler", "permissions": ["read"]},
                                      {"name": "users", "permissions": ["read"]}]

default_resources = ['app_apis', 'configuration', 'global_variables', 'workflows', 'roles', 'scheduler', 'users']


def initialize_default_resources_admin():
    """Initializes the default resources for an admin user"""
    admin = Role.query.filter(Role.id == 1).first()
    if not admin:
        admin = Role("admin", resources=default_resource_permissions_admin)
        db.session.add(admin)
    else:
        admin.set_resources(default_resource_permissions_admin)
    db.session.commit()


def initialize_default_resources_guest():
    """Initializes the default resources for a guest user"""
    guest = Role.query.filter(Role.name == "guest").first()
    if not guest:
        guest = Role("guest", resources=default_resource_permissions_guest)
        db.session.add(guest)
    else:
        guest.set_resources(default_resource_permissions_guest)
    db.session.commit()


def get_roles_by_resource_permissions(resource_permission):
    r = resource_permission.resource
    permissions = resource_permission.permissions

    roles = []
    for permission in permissions:
        roles.extend(Role.query.join(Role.resources).join(Resource.permissions).filter(
            Resource.name == r, Permission.name == permission).all())

    return {role_obj.id for role_obj in roles}


def set_resources_for_role(role_name, resources):
    """Sets the resources a role is allowed to access.

    Args:
        role_name (str): The name of the role.
        resources (dict[resource:list[permission]): A dictionary containing the name of the resource, with the value
                being a list of permission names
    """
    r = Role.query.filter(Role.name == role_name).first()
    r.set_resources(resources)


def clear_resources_for_role(role_name):
    """Clears all of the resources that a role has access to.

    Args:
        role_name (str): The name of the role.
    """
    r = Role.query.filter(Role.name == role_name).first()
    r.resources = []
    db.session.commit()


def get_all_available_resource_actions():
    """Gets a list of all of the available resource actions

    Returns:
        (list[dict]): A list of dicts containing the resource name and the actions available for that resource
    """
    resource_actions = []
    for resource_perm in default_resource_permissions_admin:
        resource_actions.append(
            {"name": resource_perm['name'], "actions": resource_perm['permissions']})
    return resource_actions


def add_user(username, password, roles=None):
    """Adds a User object.

    Args:
        username (str): The username for the User.
        password (str): The password for the User.
        roles (list[int], optional): A list of roles for the User. Defaults to None.

    Returns:
        (User): The new User object if successful, else None.
    """
    if User.query.filter_by(username=username).first() is None:
        u = User(username, password, roles=roles)
        db.session.add(u)
        db.session.commit()
        return u
    else:
        return None


def remove_user(username):
    """Removes the user.

    Args:
        username (str): The username of the User to delete.
    """
    User.query.filter_by(username=username).delete()
