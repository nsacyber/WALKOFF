import logging
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorCollection
from passlib.hash import pbkdf2_sha512
from sqlalchemy.ext.hybrid import hybrid_property

from api.server.db import Base
from api.server.db import db
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, ForeignKey, Integer, String, Enum, Boolean, DateTime
from api.server.utils.helpers import utc_as_rfc_datetime
# from api.server.db import TrackModificationsMixIn
from api.server.db.role import Role, RoleModel
from typing import List
from pydantic import BaseModel, UUID4, Any
from sqlalchemy.orm import Session
from api.server.db import get_db
from fastapi import Depends


logger = logging.getLogger(__name__)

# user_roles_association = Table('user_roles_association',
#                                   Column('role_id', Integer, ForeignKey('role.id')),
#                                   Column('user_id', Integer, ForeignKey('user.id')))


class AddUser(BaseModel):
    username: str
    password: str
    roles: List[RoleModel] = None
    active: bool = None
    resources_created: List = None


class EditUser(BaseModel):
    id: int
    username: str = None
    old_password: str = None
    password: str = None
    active: bool = None
    roles: List[RoleModel] = None


class EditPersonalUser(BaseModel):
    old_username: str
    new_username: str = None
    old_password: str = None
    password: str = None


class DisplayUser(BaseModel):
    id: int = None
    username: str = None
    active: str = None
    roles: List[int] = None


class UserModel(BaseModel):
    id: int = None
    username: str
    roles: List[RoleModel]
    _password: str
    active: bool
    last_login_at: datetime
    current_login_at: datetime
    last_login_ip: str
    current_login_ip: str
    login_count: int

    def __init__(self, name: str, password: str, role_col: AsyncIOMotorCollection, roles=None, **data: Any):
        """Initializes a new User object

        Args:
            name (str): The username for the User.
            password (str): The password for the User.
            roles (list[int], optional): List of Role ids for the User. Defaults to None.
        """
        super().__init__(**data)
        self.username = name
        self._password = pbkdf2_sha512.hash(password)
        self.roles = []
        if roles:
            self.set_roles(roles, role_col)

    @hybrid_property
    def password(self):
        """Returns the password for the user.

        Returns:
            (str): The password
        """
        return self._password

    @password.setter
    def password(self, new_password):
        """Sets the password for a user, and encrypts it.

        Args:
            new_password (str): The new password for the User.
        """
        self._password = pbkdf2_sha512.hash(new_password)

    def verify_password(self, password_attempt):
        """Verifies that the input password matches with the stored password.

        Args:
            password_attempt(str): The input password.

        Returns:
            (bool): True if the passwords match, False if not.
        """
        return pbkdf2_sha512.verify(password_attempt, self._password)

    def set_roles(self, new_roles, role_col):
        """Sets the roles for a User.

        Args:
            new_roles (list[int]|set(int)): A list of Role IDs for the User.
        """

        new_role_ids = set(new_roles)

        ret = []
        for id in new_role_ids:
            new_roles.append(await role_col.find_one({"id": id}, projection={'_id': False}))

        self.roles[:] = ret

        roles_not_added = new_role_ids - {role.id for role in new_roles}
        if roles_not_added:
            logger.warning(f"Cannot add roles {roles_not_added} to user {self.id}. Roles do not exist")

    def login(self, ip_address):
        """Tracks login information for the User upon logging in.

        Args:
            ip_address (str): The IP address from which the User logged in.
        """
        self.last_login_at = self.current_login_at
        self.current_login_at = datetime.utcnow()
        self.last_login_ip = self.current_login_ip
        self.current_login_ip = ip_address
        self.login_count += 1

    def logout(self):
        """Tracks login/logout information for the User upon logging out"""
        if self.login_count > 0:
            self.login_count -= 1
        else:
            logger.warning(f"User {self.id} logged out, but login count was already at 0")

    def has_role(self, role):
        """Checks if a User has a Role associated with it.

        Args:
            role (int): The ID of the Role.

        Returns:
            (bool): True if the User has the Role, False otherwise.
        """
        return role in [role.id for role in self.roles]

