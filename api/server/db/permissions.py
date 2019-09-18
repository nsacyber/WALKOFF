import logging
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
    permissions: List[RolePermissions]
    _walkoff_type: str = "permissions"


def creator_only_permissions(creator):
    return PermissionsModel(creator=creator,
                            access_level=AccessLevel.CREATOR_ONLY,
                            permissions=[])
