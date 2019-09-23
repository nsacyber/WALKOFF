import logging
from copy import deepcopy
from typing import List
from enum import Enum

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AccessLevel(int, Enum):
    CREATOR_ONLY = 0
    EVERYONE = 1
    ROLE_BASED = 2


class RolePermissions(BaseModel):
    role: int
    permissions: List[str]


class PermissionsModel(BaseModel):
    creator: int = None
    access_level: int
    role_permissions: List[RolePermissions]
    _walkoff_type: str = "permissions"


def creator_only_permissions(creator):
    internal = {'role': 1, 'permissions': ["delete", "execute", "read", "update"]}
    internal_user_permission = RolePermissions(**internal)
    super_user = {'role': 2, 'permissions': ["delete", "execute", "read", "update"]}
    super_user_permission = RolePermissions(**super_user)
    return PermissionsModel(creator=creator,
                            access_level=AccessLevel.CREATOR_ONLY,
                            role_permissions=[internal_user_permission, super_user_permission])


def default_permissions(curr_user_id, walkoff_db, resource_name):
    role_col = walkoff_db.roles
    roles = await role_col.find().to_list(None)
    role_permissions = []

    for role_elem in roles:
        for resource in role_elem['resources']:
            if resource["name"] == resource_name:
                role_permissions = resource["permissions"]
        data = {'role': role_elem["id"], 'permissions': role_permissions}
        role_permissions.append(RolePermissions(**data))
    return PermissionsModel(creator=curr_user_id,
                            access_level=AccessLevel.ROLE_BASED,
                            role_permissions=role_permissions)


def auth_check(curr_user_id: int, resource_id: str, permission: str, resource_name: str, walkoff_db):
    user_col = walkoff_db.users
    resource_col = walkoff_db.resource_name

    curr_user = await user_col.find_one({"id": curr_user_id}, projection={'_id': False})
    curr_roles = curr_user["roles"]

    resource = await resource_col.find_one({"id_": resource_id}, projection={'_id': False})
    if resource:
        permission_model = resource["permissions"]
        if permission_model["creator"] == curr_user_id:
            return True

        role_permissions = permission_model["role_permissions"]
        for role_perm_elem in role_permissions:
            if role_perm_elem["role"] in curr_roles:
                if permission in role_perm_elem["permissions"]:
                    return True

        return False

    else:
        return False
