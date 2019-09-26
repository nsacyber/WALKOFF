import logging
from copy import deepcopy
from typing import List
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from api.server.db.role import DefaultRoleUUID
from api.server.db.user import UserModel
from common import mongo_helpers

logger = logging.getLogger(__name__)


class AccessLevel(int, Enum):
    CREATOR_ONLY = 0
    EVERYONE = 1
    ROLE_BASED = 2


class RolePermissions(BaseModel):
    role: UUID
    permissions: List[str]


class PermissionsModel(BaseModel):
    creator: UUID = None
    access_level: int
    role_permissions: List[RolePermissions] = None
    _walkoff_type: str = "permissions"


async def creator_only_permissions(creator):
    internal = {'role': DefaultRoleUUID.INTERNAL_USER.value, 'permissions': ["delete", "execute", "read", "update"]}
    internal_user_permission = RolePermissions(**internal)
    super_user = {'role': DefaultRoleUUID.SUPER_ADMIN.value, 'permissions': ["delete", "execute", "read", "update"]}
    super_user_permission = RolePermissions(**super_user)
    return PermissionsModel(creator=creator,
                            access_level=AccessLevel.CREATOR_ONLY,
                            role_permissions=[internal_user_permission, super_user_permission])


async def default_permissions(curr_user_id, walkoff_db, resource_name):
    role_col = walkoff_db.roles
    roles = await role_col.find().to_list(None)
    role_permissions = []
    permissions_elem = []

    for role_elem in roles:
        for resource in role_elem['resources']:
            if resource["name"] == resource_name:
                permissions_elem = resource["permissions"]
        data = {'role': role_elem["id_"], 'permissions': permissions_elem}
        role_permissions.append(RolePermissions(**data))
    return PermissionsModel(creator=curr_user_id,
                            access_level=AccessLevel.EVERYONE,
                            role_permissions=role_permissions)


async def auth_check(resource, curr_user_id: UUID, permission: str, walkoff_db):
    user_col = walkoff_db.users
    curr_user = await mongo_helpers.get_item(user_col, UserModel, curr_user_id)
    curr_roles = curr_user.roles

    if resource:
        permission_model = resource.permissions
        if permission_model.creator == curr_user_id:
            return True

        role_permissions = permission_model.role_permissions
        for role_perm_elem in role_permissions:
            if role_perm_elem.role in curr_roles:
                if permission in role_perm_elem.permissions:
                    return True

        return False

    else:
        return False
