import logging
from typing import List
from enum import Enum

from pydantic import BaseModel, UUID4

logger = logging.getLogger(__name__)


class AccessLevel(int, Enum):
    CREATOR_ONLY = 0
    EVERYONE = 1
    ROLE_BASED = 2


class PermissionVerb(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


class RolePermissions(BaseModel):
    role: int
    permissions: List[PermissionVerb]


class PermissionsModel(BaseModel):
    creator: UUID4
    access_level: AccessLevel
    permissions: List[RolePermissions]
    _walkoff_type: str = "permissions"


rude_perms = [
    PermissionVerb.READ,
    PermissionVerb.UPDATE,
    PermissionVerb.DELETE,
    PermissionVerb.EXECUTE
]


def creator_only_permissions(creator):
    return PermissionsModel(creator=creator,
                            access_level=AccessLevel.CREATOR_ONLY,
                            permissions=[RolePermissions(role=1, permissions=rude_perms)])


def role_based_permissions(creator):
    return PermissionsModel(creator=creator,
                            access_level=AccessLevel.ROLE_BASED,
                            permissions=[])


def everyone_permissions():
    return PermissionsModel(creator=None,
                            access_level=AccessLevel.EVERYONE,
                            permissions=[])
