import logging
from datetime import datetime
from typing import List
from uuid import UUID

import pymongo
from passlib.hash import pbkdf2_sha512
from pydantic import BaseModel, validator

from api.server.db import IDBaseModel
from api.server.db.mongo import mongo

logger = logging.getLogger("API")


class EditUser(BaseModel):
    username: str = ""
    new_username: str = ""
    old_password: str = ""
    new_password: str = ""
    active: bool = True
    roles: List[UUID] = []


class EditPersonalUser(BaseModel):
    new_username: str = ""
    old_password: str = ""
    new_password: str = ""


class UserModel(IDBaseModel):
    id_: UUID = None
    hashed: bool = False
    username: str
    password: str = None
    roles: List[UUID]
    active: bool = True
    last_login_at: datetime = None
    current_login_at: datetime = None
    last_login_ip: str = None
    current_login_ip: str = None
    login_count: int = 0
    _name_field = "username"

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
        roles_col: pymongo.collection.Collection = mongo.reg_client.walkoff_db.roles
        for role in roles:
            if not roles_col.find_one({"id_": role}):
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
