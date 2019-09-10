import logging
from datetime import datetime

from passlib.hash import pbkdf2_sha512
from sqlalchemy.ext.hybrid import hybrid_property

from api.server.db import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Enum, Boolean, DateTime
from api_gateway.helpers import utc_as_rfc_datetime
from api_gateway.serverdb.mixins import TrackModificationsMixIn
from api_gateway.serverdb.role import Role
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from api.server.db import get_db
from fastapi import Depends


logger = logging.getLogger(__name__)

user_roles_association = Base.Table('user_roles_association',
                                  Column('role_id', Integer, ForeignKey('role.id')),
                                  Column('user_id', Integer, ForeignKey('user.id')))


class UserModel(BaseModel):
    id: UUID4
    username: str
    _password: str
    active: bool
    last_login_at: DateTime
    current_login_at: DateTime
    last_login_ip: str
    current_login_ip: str
    login_count: int


class User(Base, TrackModificationsMixIn):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # roles = relationship('Role', secondary=user_roles_association, backref=db.backref('users', lazy='dynamic'))
    roles = relationship('Role', back_populates='users')
    username = Column(String(80), unique=True, nullable=False)
    _password = Column('password', String(255), nullable=False)
    active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)
    current_login_at = Column(DateTime)
    last_login_ip = Column(String(45))
    current_login_ip = Column(String(45))
    login_count = Column(Integer, default=0)

    def __init__(self, name, password, roles=None):
        """Initializes a new User object

        Args:
            name (str): The username for the User.
            password (str): The password for the User.
            roles (list[int], optional): List of Role ids for the User. Defaults to None.
        """
        self.username = name
        self._password = pbkdf2_sha512.hash(password)
        self.roles = []
        if roles:
            self.set_roles(roles)

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

    def set_roles(self, new_roles):
        """Sets the roles for a User.

        Args:
            new_roles (list[int]|set(int)): A list of Role IDs for the User.
        """

        new_role_ids = set(new_roles)
        new_roles = Role.query.filter(Role.id.in_(new_role_ids)).all() if new_role_ids else []

        self.roles[:] = new_roles

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

    def logout(self, db_session: Session = Depends(get_db)):
        """Tracks login/logout information for the User upon logging out"""
        if self.login_count > 0:
            self.login_count -= 1
        else:
            logger.warning(f"User {self.id} logged out, but login count was already at 0")
        db_session.commit()

    def has_role(self, role):
        """Checks if a User has a Role associated with it.

        Args:
            role (int): The ID of the Role.

        Returns:
            (bool): True if the User has the Role, False otherwise.
        """
        return role in [role.id for role in self.roles]

    def as_json(self, with_user_history=False):
        """Returns the dictionary representation of a User object.

        Args:
            with_user_history (bool, optional): Boolean to determine whether or not to include user history in the JSON
                representation of the User. Defaults to False.

        Returns:
            (dict): The dictionary representation of a User object.
        """
        out = {"id": self.id,
               "username": self.username,
               "roles": [role.as_json() for role in self.roles],
               "active": self.active}
        if with_user_history:
            out.update({
                "last_login_at": utc_as_rfc_datetime(self.last_login_at),
                "current_login_at": utc_as_rfc_datetime(self.current_login_at),
                "last_login_ip": self.last_login_ip,
                "current_login_ip": self.current_login_ip,
                "login_count": self.login_count})
        return out

    def permission_json(self):
        """Returns the dictionary representation of a User's permissions.

        Args:
            with_user_history (bool, optional): Boolean to determine whether or not to include user history in the JSON
                representation of the User. Defaults to False.

        Returns:
            (dict): The dictionary representation of a User's permissions.
        """
        out = {"roles": [role.as_json() for role in self.roles]}
        return out
