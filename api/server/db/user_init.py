from enum import Enum

from common.config import config
from common.helpers import preset_uuid

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
    {"name": "users", "permissions": ["create", "read", "update", "delete"]},
    {"name": "umpire", "permissions": ["create", "read", "update", "delete"]}
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
    {"name": "users", "permissions": ["create", "read", "update", "delete"]},
    {"name": "umpire", "permissions": ["create", "read", "update", "delete"]}
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
    {"name": "users", "permissions": ["create", "read", "update", "delete"]},
    {"name": "umpire", "permissions": ["create", "read", "update", "delete"]}
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
    {"name": "users", "permissions": ["read"]},
    {"name": "umpire", "permissions": ["create", "read", "update", "delete"]}
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
    {"name": "users", "permissions": ["read"]},
    {"name": "umpire", "permissions": ["read"]}
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
    {"name": "users", "permissions": ["read"]},
    {"name": "umpire", "permissions": []}
]



class DefaultRoleUUID(Enum):
    INTERNAL_USER = preset_uuid("internal_role")
    SUPER_ADMIN = preset_uuid("sadmin_role")
    ADMIN = preset_uuid("admin_role")
    APP_DEV = preset_uuid("app_dev_role")
    WF_DEV = preset_uuid("wf_dev_role")
    WF_OP = preset_uuid("wf_op_role")


DefaultRoleUUIDS = [v.value for v in DefaultRoleUUID.__members__.values()]


default_roles = {
    "internal_user_role": {"id_": DefaultRoleUUID.INTERNAL_USER.value,
                           "name": "internal_user", "description": "Used by WALKOFF components.",
                           "resources": default_resource_permissions_internal_user},
    "super_admin_role": {"id_": DefaultRoleUUID.SUPER_ADMIN.value,
                         "name": "super_admin", "description": "Permanent admin role.",
                         "resources": default_resource_permissions_super_admin},
    "admin_role": {"id_": DefaultRoleUUID.ADMIN.value,
                   "name": "admin", "description": "General admin role.",
                   "resources": default_resource_permissions_admin},
    "app_developer_role": {"id_": DefaultRoleUUID.APP_DEV.value,
                           "name": "app_developer", "description": "Provides access to the App Editor.",
                           "resources": default_resource_permissions_app_developer},
    "workflow_developer_role": {"id_": DefaultRoleUUID.WF_DEV.value,
                                "name": "workflow_developer",
                                "description": "Provides access to the Workflow Editor",
                                "resources": default_resource_permissions_workflow_developer},
    "workflow_operator_role": {"id_": DefaultRoleUUID.WF_OP.value,
                               "name": "workflow_operator",
                               "description": "Only provides access to run Workflows.",
                               "resources": default_resource_permissions_workflow_operator}
}

class DefaultUserUUID(Enum):
    INTERNAL_USER = preset_uuid("internal_user")
    SUPER_ADMIN = preset_uuid("sadmin_user")
    ADMIN = preset_uuid("admin_user")


DefaultUserUUIDS = [v.value for v in DefaultUserUUID.__members__.values()]

default_users = {
    "internal_user": {"id_": DefaultUserUUID.INTERNAL_USER.value,
                      "username": "internal_user", "password": config.get_from_file(config.INTERNAL_KEY_PATH),
                      "hashed": False, "roles": [DefaultRoleUUID.INTERNAL_USER.value]},
    "super_admin": {"id_": DefaultUserUUID.SUPER_ADMIN.value,
                    "username": "super_admin", "password": "super_admin",
                    "hashed": False, "roles": [DefaultRoleUUID.SUPER_ADMIN.value]},
    "admin": {"id_": DefaultUserUUID.ADMIN.value,
              "username": "admin", "password": "admin",
              "hashed": False, "roles": [DefaultRoleUUID.ADMIN.value]}
}

default_resources = ['app_apis', 'apps', 'settings', 'global_variables', 'workflows', 'roles', 'scheduler', 'users']


# async def initialize_default_resources_internal_user(roles_col: AsyncIOMotorCollection):
#     """Initializes the default resources for an internal user"""
#     internal_user = RoleModel(**(await roles_col.find_one({"id": 1}, projection={'_id': False})))
#     if not internal_user:
#         data = default_internal_user_role
#         internal_user = RoleModel(**data)
#         roles_col.insert_one(dict(internal_user))
#     else:
#         internal_user.set_resources(default_resource_permissions_internal_user, roles_col)
#
#
# async def initialize_default_resources_super_admin(roles_col: AsyncIOMotorCollection):
#     """Initializes the default resources for a super admin user"""
#     super_admin = RoleModel(**(await roles_col.find_one({"id": 2}, projection={'_id': False})))
#     if not super_admin:
#         data = default_super_admin_role
#         super_admin = RoleModel(**data)
#         roles_col.insert_one(dict(super_admin))
#     else:
#         super_admin.set_resources(default_resource_permissions_super_admin, roles_col)
#
#
# async def initialize_default_resources_admin(roles_col: AsyncIOMotorCollection):
#     """Initializes the default resources for an admin user"""
#     admin = RoleModel(**(await roles_col.find_one({"id": 3}, projection={'_id': False})))
#     if not admin:
#         data = default_admin_role
#         admin = RoleModel(**data)
#         roles_col.insert_one(dict(admin))
#     else:
#         admin.set_resources(default_resource_permissions_admin, roles_col)
#
#
# async def initialize_default_resources_app_developer(roles_col: AsyncIOMotorCollection):
#     """Initializes the default resources for an app developer"""
#     app_developer = RoleModel(**(await roles_col.find_one({"id": 4}, projection={'_id': False})))
#     if not app_developer:
#         data =
#         app_developer = RoleModel(**data)
#         roles_col.insert_one(dict(app_developer))
#     else:
#         app_developer.set_resources(default_resource_permissions_app_developer, roles_col)
#
#
# async def initialize_default_resources_workflow_developer(roles_col: AsyncIOMotorCollection):
#     """Initializes the default resources for a workflow developer"""
#     workflow_developer = RoleModel(**(await roles_col.find_one({"id": 5}, projection={'_id': False})))
#     if not workflow_developer:
#         data =
#         workflow_developer = RoleModel(**data)
#         roles_col.insert_one(dict(workflow_developer))
#     else:
#         workflow_developer.set_resources(default_resource_permissions_workflow_developer, roles_col)
#
#
# async def initialize_default_resources_workflow_operator(roles_col: AsyncIOMotorCollection):
#     """Initializes the default resources for a workflow operator"""
#     workflow_operator = RoleModel(**(await roles_col.find_one({"id": 6}, projection={'_id': False})))
#     if not workflow_operator:
#         data =
#         workflow_operator = RoleModel(**data)
#         roles_col.insert_one(dict(workflow_operator))
#     else:
#         workflow_operator.set_resources(default_resource_permissions_workflow_operator, roles_col)


# async def set_resources_for_role(role_name: str, resources: dict, roles_col: AsyncIOMotorCollection):
#     """Sets the resources a role is allowed to access.
#
#     Args:
#         role_name (str): The name of the role.
#         resources (dict[resource:list[permission]): A dictionary containing the name of the resource, with the value
#                 being a list of permission names
#     """
#     r = RoleModel(**(await roles_col.find_one({"name": role_name}, projection={'_id': False})))
#     r.set_resources(resources, roles_col)
#
#
# async def clear_resources_for_role(role_name: str, roles_col: AsyncIOMotorCollection):
#     """Clears all of the resources that a role has access to.
#
#     Args:
#         role_name (str): The name of the role.
#     """
#     r = RoleModel(**(await roles_col.find_one({"name": role_name}, projection={'_id': False})))
#     r.set_resources([], roles_col)




# async def add_user(username: str, password: str, walkoff_db: AsyncIOMotorDatabase, roles: list = None):
#     """Adds a User object.
#
#     Args:
#         username (str): The username for the User.
#         password (str): The password for the User.
#         roles (list[int], optional): A list of roles for the User. Defaults to None.
#
#     Returns:
#         (User): The new User object if successful, else None.
#     """
#     user_col = walkoff_db.users
#     role_col = walkoff_db.roles
#
#     user = await user_col.find_one({"username": username}, projection={'_id': False})
#     if user is None:
#         u = UserModel(username, password, roles=roles, role_col=role_col, user)
#         user_col.insert_one(**dict(u))
#         return u
#     else:
#         return None


# async def remove_user(username: str, user_col: AsyncIOMotorCollection):
#     """Removes the user.
#
#     Args:
#         username (str): The username of the User to delete.
#     """
#     to_delete = user_col.find_one({"username": username}, projection={'_id': False})
#     user_col.delete_one(dict(to_delete))
