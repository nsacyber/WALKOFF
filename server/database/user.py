import logging
from datetime import datetime
from passlib.hash import pbkdf2_sha512
from sqlalchemy.ext.hybrid import hybrid_property

from server.extensions import db
from server.database.mixins import TrackModificationsMixIn
from server.database.role import Role

logger = logging.getLogger(__name__)


user_roles_association = db.Table('user_roles_association',
                                  db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')))


class User(db.Model, TrackModificationsMixIn):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roles = db.relationship('Role', secondary=user_roles_association, backref=db.backref('users', lazy='dynamic'))
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password = db.Column('password', db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    current_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer, default=0)

    def __init__(self, name, password, roles=None):
        """Initializes a new User object

        Args:
            name (str): The username for the User.
            password (str): The password for the User.
            roles (list[int]): List of Role ids for the User. Defaults to None.
        """
        self.username = name
        self._password = pbkdf2_sha512.hash(password)
        self.roles = []
        if roles:
            self.set_roles(roles)

    @hybrid_property
    def password(self):
        """Returns the password for the user.
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
            True if the passwords match, False if not.
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
            logger.warning('Cannot add roles {0} to user {1}. Roles do not exist'.format(roles_not_added, self.id))

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
        """Tracks login/logout information for the User upon logging out.
        """
        if self.login_count > 0:
            self.login_count -= 1
        else:
            logger.warning('User {} logged out, but login count was already at 0'.format(self.id))
        db.session.commit()

    def has_role(self, role):
        """Checks if a User has a Role associated with it.

        Args:
            role (int): The ID of the Role.

        Returns:
            True if the User has the Role, False otherwise.
        """
        return role in [role.id for role in self.roles]

    def as_json(self, with_user_history=False):
        """Returns the dictionary representation of a User object.

        Args:
            with_user_history (bool, optional): Boolean to determine whether or not to include user history in the JSON
                representation of the User. Defaults to False.

        Returns:
            The dictionary representation of a User object.
        """
        out = {"id": self.id,
               "username": self.username,
               "roles": [role.as_json() for role in self.roles],
               "active": self.active}
        if with_user_history:
            out.update({
                "last_login_at": self.last_login_at,
                "current_login_at": self.current_login_at,
                "last_login_ip": self.last_login_ip,
                "current_login_ip": self.current_login_ip,
                "login_count": self.login_count})
        return out
