import logging
from datetime import datetime
from enum import Enum
from typing import Union

from motor.motor_asyncio import AsyncIOMotorCollection
from passlib.hash import pbkdf2_sha512

from api.server.utils.helpers import utc_as_rfc_datetime
# from api.server.db import TrackModificationsMixIn
from api.server.db.role import RoleModel
from typing import List
from pydantic import BaseModel, Any, validator, Schema
from api.server.db import mongo
from fastapi import Depends


logger = logging.getLogger(__name__)

# user_roles_association = Table('user_roles_association',
#                                   Column('role_id', Integer, ForeignKey('role.id')),
#                                   Column('user_id', Integer, ForeignKey('user.id_')))

# class AddUser(BaseModel):
#     username: str
#     password: str
#     roles: List[RoleModel] = None
#     active: bool = None


class DefaultUsers(int, Enum):
    INTERNAL_USER = 1
    SUPER_ADMIN = 2
    ADMIN = 3


PROTECTED_USERS = range(DefaultUsers.INTERNAL_USER, DefaultUsers.ADMIN)


class EditUser(BaseModel):
    id_: int
    username: str = ""
    new_username: str = ""
    old_password: str = ""
    new_password: str = ""
    active: bool = True
    roles: List[RoleModel] = []


class EditPersonalUser(BaseModel):
    new_username: str = ""
    old_password: str = ""
    new_password: str = ""


# class DisplayUser(BaseModel):
#     id_: int = None
#     username: str = None
#     active: str = None
#     roles: List[int] = None


class UserModel(BaseModel):
    id_: int
    hashed: bool = False
    username: str
    password: str = None
    roles: List[int]
    active: bool = True
    last_login_at: datetime = None
    current_login_at: datetime = None
    last_login_ip: str = None
    current_login_ip: str = None
    login_count: int = 0
    _secondary_id = "username"

    @validator('password')
    def hash_pass(cls, password, values):
        if not values:
            return password
        if values.get("hashed") and not password:
            return password

        if values.get("hashed") and not password.startswith("$pbkdf2-sha512$25000$"):
            raise ValueError("Hashed password not in expected format.")
        elif not values.get("hashed") and password.startswith("$pbkdf2-sha512$25000$"):
            raise ValueError("Got a hashed password but hashed flag was unset.")
        elif not values.get("hashed"):
            values["hashed"] = True
            r = pbkdf2_sha512.hash(password)
            return r
        else:
            return password

    @validator('roles', whole=True)
    def verify_roles_exist(cls, roles):
        roles_coll: AsyncIOMotorCollection = mongo.client.walkoff_db.roles
        for role in roles:
            if not roles_coll.find_one({"id_": role}):
                raise ValueError(f"Role {role} does not exist.")

        return roles

    async def verify_password(self, password_attempt: str):
        """Verifies that the input password matches with the stored password.

        Args:
            password_attempt(str): The input password.

        Returns:
            (bool): True if the passwords match, False if not.
        """

        return pbkdf2_sha512.verify(password_attempt, self.password)

    async def hash_and_set_password(self, password: str):
        """Verifies that the input password matches with the stored password.

        Args:
            password_attempt(str): The input password.

        Returns:
            (bool): True if the passwords match, False if not.
        """

        self.password = pbkdf2_sha512.hash(password)


    # async def set_roles(self, new_roles, role_col):
    #     """Sets the roles for a User.
    #
    #     Args:
    #         new_roles (list[int]|set(int)): A list of Role IDs for the User.
    #     """
    #
    #     new_role_ids = set(new_roles)
    #
    #     ret = []
    #     for id_ in new_role_ids:
    #         new_roles.append(await role_col.find_one({"id_": id_}, projection={'_id': False}))
    #
    #     self.roles[:] = ret
    #
    #     roles_not_added = new_role_ids - {role.id_ for role in new_roles}
    #     if roles_not_added:
    #         logger.warning(f"Cannot add roles {roles_not_added} to user {self.id_}. Roles do not exist")

    async def login(self, ip_address):
        """Tracks login information for the User upon logging in.

        Args:
            ip_address (str): The IP address from which the User logged in.
        """
        self.last_login_at = self.current_login_at
        self.current_login_at = datetime.utcnow()
        self.last_login_ip = self.current_login_ip
        self.current_login_ip = ip_address
        self.login_count += 1

    async def logout(self):
        """Tracks login/logout information for the User upon logging out"""
        if self.login_count > 0:
            self.login_count -= 1
        else:
            logger.warning(f"User {self.id_} logged out, but login count was already at 0")

    # async def has_role(self, role):
    #     """Checks if a User has a Role associated with it.
    #
    #     Args:
    #         role (int): The ID of the Role.
    #
    #     Returns:
    #         (bool): True if the User has the Role, False otherwise.
    #     """
    #     return role in [role.id_ for role in self.roles]
    #
