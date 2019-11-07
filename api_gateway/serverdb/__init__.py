import logging

from api_gateway.extensions import db
from api_gateway.serverdb.resource import Resource, Permission
from api_gateway.serverdb.role import Role
from api_gateway.serverdb.user import User

# TODO: Migrate this all to SQLAlchemy for the sanic migration. Probably combine walkoff and execution dbs
logger = logging.getLogger(__name__)

default_resource_permissions_internal_user = [
    {"name": "app_apis", "permissions": ["create", "read", "update", "delete"]},
    {"name": "apps", "permissions": ["create", "read", "update", "delete"]},
    {"name": "settings", "permissions": ["read", "update"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["create", "read", "update", "delete"]},
    {"name": "roles", "permissions": ["create", "read", "update", "delete"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["create", "read", "update", "delete"]}
]

default_resource_permissions_super_admin = [
    {"name": "app_apis", "permissions": ["create", "read", "update", "delete"]},
    {"name": "apps", "permissions": ["create", "read", "update", "delete"]},
    {"name": "settings", "permissions": ["read", "update"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["create", "read", "update", "delete"]},
    {"name": "roles", "permissions": ["create", "read", "update", "delete"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["create", "read", "update", "delete"]}
]


default_resource_permissions_admin = [
    {"name": "app_apis", "permissions": ["create", "read", "update", "delete"]},
    {"name": "apps", "permissions": ["create", "read", "update", "delete"]},
    {"name": "settings", "permissions": ["read", "update"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["create", "read", "update", "delete"]},
    {"name": "roles", "permissions": ["create", "read", "update", "delete"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["create", "read", "update", "delete"]}
]

default_resource_permissions_app_developer = [
    {"name": "app_apis", "permissions": ["read"]},
    {"name": "apps", "permissions": ["create", "read", "update", "delete"]},
    {"name": "settings", "permissions": ["read"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["read"]},
    {"name": "roles", "permissions": ["read"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["read"]}
]

default_resource_permissions_workflow_developer = [
    {"name": "app_apis", "permissions": ["read"]},
    {"name": "apps", "permissions": []},
    {"name": "settings", "permissions": ["read"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["read"]},
    {"name": "roles", "permissions": ["read"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["read"]}
]

default_resource_permissions_workflow_operator = [
    {"name": "app_apis", "permissions": ["read"]},
    {"name": "apps", "permissions": []},
    {"name": "settings", "permissions": ["read"]},
    {"name": "global_variables", "permissions": ["execute"]},
    {"name": "workflow_variables", "permissions": ["read", "update"]},
    {"name": "workflows", "permissions": ["read", "execute"]},
    {"name": "dashboards", "permissions": ["read", "update"]},
    {"name": "workflowstatus", "permissions": ["read"]},
    {"name": "roles", "permissions": ["read"]},
    {"name": "scheduler", "permissions": ["read"]},
    {"name": "users", "permissions": ["read"]}
]

default_resources = ['app_apis', 'apps', 'settings', 'global_variables', 'workflows', 'roles', 'scheduler', 'users']


def initialize_default_resources_internal_user():
    """Initializes the default resources for an internal user"""
    internal_user = Role.query.filter(Role.id == 1).first()
    if not internal_user:
        internal_user = Role("internal_user", description="Placeholder description",
                             resources=default_resource_permissions_internal_user)
        db.session.add(internal_user)
    else:
        internal_user.set_resources(default_resource_permissions_internal_user)
    db.session.commit()


def initialize_default_resources_super_admin():
    """Initializes the default resources for a super admin user"""
    super_admin = Role.query.filter(Role.id == 2).first()
    if not super_admin:
        super_admin = Raole("super_admin", description="Placeholder description",
                           resources=default_resource_permissions_super_admin)
        db.session.add(super_admin)
    else:
        super_admin.set_resources(default_resource_permissions_super_admin)
    db.session.commit()


def initialize_default_resources_admin():
    """Initializes the default resources for an admin user"""
    admin = Role.query.filter(Role.id == 3).first()
    if not admin:
        admin = Role("admin", description="Placeholder description", resources=default_resource_permissions_admin)
        db.session.add(admin)
    else:
        admin.set_resources(default_resource_permissions_admin)
    db.session.commit()


def initialize_default_resources_app_developer():
    """Initializes the default resources for an app developer"""
    app_developer = Role.query.filter(Role.id == 4).first()
    if not app_developer:
        app_developer = Role("app_developer", description="Placeholder description",
                                  resources=default_resource_permissions_app_developer)
        db.session.add(app_developer)
    else:
        app_developer.set_resources(default_resource_permissions_app_developer)
    db.session.commit()


def initialize_default_resources_workflow_developer():
    """Initializes the default resources for a workflow developer"""
    workflow_developer = Role.query.filter(Role.id == 5).first()
    if not workflow_developer:
        workflow_developer = Role("workflow_developer", description="Placeholder description",
                                  resources=default_resource_permissions_workflow_developer)
        db.session.add(workflow_developer)
    else:
        workflow_developer.set_resources(default_resource_permissions_workflow_developer)
    db.session.commit()


def initialize_default_resources_workflow_operator():
    """Initializes the default resources for a workflow operator"""
    workflow_operator = Role.query.filter(Role.id == 6).first()
    if not workflow_operator:
        workflow_operator = Role("workflow_operator", description="Placeholder description",
                                 resources=default_resource_permissions_workflow_operator)
        db.session.add(workflow_operator)
    else:
        workflow_operator.set_resources(default_resource_permissions_workflow_operator)
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
