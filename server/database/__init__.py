import logging

from server.extensions import db
from .user import User
from .role import Role
from .resource import Resource, Permission


logger = logging.getLogger(__name__)

default_resource_permissions = [{"name": "app_apis", "permissions": ["read"]},
                                {"name": "cases", "permissions": ["create", "read", "update", "delete"]},
                                {"name": "configuration", "permissions": ["read", "update"]},
                                {"name": "devices", "permissions": ["create", "read", "update", "delete"]},
                                {"name": "messages", "permissions": ["create", "read", "update", "delete"]},
                                {"name": "metrics", "permissions": ["read"]},
                                {"name": "playbooks", "permissions": ["create", "read", "update", "delete", "execute"]},
                                {"name": "roles", "permissions": ["read"]},
                                {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
                                {"name": "users", "permissions": ["create", "read", "update", "delete"]}]


default_resources = ['app_apis', 'cases', 'configuration', 'devices', 'messages', 'metrics', 'playbooks', 'roles',
                     'scheduler', 'users']


def initialize_default_resources_for_admin():
    admin = Role.query.filter(Role.name == "admin").first()
    if not admin:
        admin = Role("admin", resources=default_resource_permissions)
        db.session.add(admin)
    else:
        admin.set_resources(default_resource_permissions)
    db.session.commit()


def get_roles_by_resource_permissions(resource_permission):
    resource = resource_permission.resource
    permissions = resource_permission.permissions

    roles = []
    for permission in permissions:
        roles.extend(Role.query.join(Role.resources).join(Resource.permissions).filter(Resource.name == resource,
                                                                                       Permission.name == permission).all())

    return set([role.name for role in roles])


def set_resources_for_role(role_name, resources):
    """Sets the resources a role is allowed to access.

    Args:
        role_name (str): The name of the role.
        resources (dict[resource:list[permission]): A dictionary containing the name of the resource, with the value
                being a list of permission names
    """
    role = Role.query.filter(Role.name == role_name).first()
    role.set_resources(resources)


def clear_resources_for_role(role_name):
    """Clears all of the resources that a role has access to.

    Args:
        role_name (str): The name of the role.
    """
    role = Role.query.filter(Role.name == role_name).first()
    role.resources = []
    db.session.commit()


def get_all_available_resource_actions():
    resource_actions = []
    for resource_perm in default_resource_permissions:
        resource_actions.append(
            {"name": resource_perm['name'], "actions": resource_perm['permissions']})
    return resource_actions


def add_user(username, password, roles=None):
    """Adds a User object.

    Args:
        username (str): The username for the User.
        password (str): The password for the User.
        roles (list[str]): A list of roles for the User.

    Returns:
        The new User object if successful, else None.
    """
    if User.query.filter_by(username=username).first() is None:
        user = User(username, password, roles=roles)
        db.session.add(user)
        db.session.commit()
        return user
    else:
        return None


def remove_user(username):
    """Removes the user.

    Args:
        username (str): The username of the User to delete.
    """
    User.query.filter_by(username=username).delete()
