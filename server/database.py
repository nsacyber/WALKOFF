import logging
from datetime import datetime

import flask_sqlalchemy
from passlib.hash import pbkdf2_sha512
from sqlalchemy.ext.hybrid import hybrid_property

logger = logging.getLogger(__name__)

db = flask_sqlalchemy.SQLAlchemy()

default_resources = ['/', 'playbooks', 'configuration', 'interface', 'trigger', 'metrics', 'users', 'cases', 'apps',
                     'scheduler']
default_permissions = ['create', 'read', 'update', 'delete', 'execute']


def initialize_resource_permissions_from_default():
    resource_permissions = []
    for resource in default_resources:
        resource_permissions.append({'name': resource, 'permissions': list(default_permissions)})
    return resource_permissions


default_resource_permissions = initialize_resource_permissions_from_default()


def initialize_default_resources_for_admin():
    admin = Role.query.filter(Role.name == "admin").first()
    if not admin:
        admin = Role("admin", resources=default_resource_permissions)
        db.session.add(admin)
    else:
        admin.set_resources(default_resource_permissions)
    db.session.commit()


def get_roles_by_resource_permissions(resource_permission):
    resource = resource_permission.resource
    permissions = resource_permission.permissions

    roles = []
    for permission in permissions:
        roles.extend(Role.query.join(Role.resources).join(Resource.permissions).filter(Resource.name == resource,
                                                                                       Permission.name == permission).all())

    return set([role.name for role in roles])


def set_resources_for_role(role_name, resources):
    """Sets the resources a role is allowed to access.

    Args:
        role_name (str): The name of the role.
        resources (dict[resource:list[permission]): A dictionary containing the name of the resource, with the value
                being a list of permission names
    """
    role = Role.query.filter(Role.name == role_name).first()
    role.set_resources(resources)


def clear_resources_for_role(role_name):
    """Clears all of the resources that a role has access to.

    Args:
        role_name (str): The name of the role.
    """
    role = Role.query.filter(Role.name == role_name).first()
    role.resources = []
    db.session.commit()


user_roles_association = db.Table('user_roles_association',
                                  db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')))


class TrackModificationsMixIn(object):
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


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
            roles (list[str]): List of Role names for the User. Defaults to None.
        """
        self.username = name
        self._password = pbkdf2_sha512.hash(password)
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
            new_roles (list[str]): A list of Role names for the User.
        """
        self.roles[:] = []

        new_role_names = set(new_roles)
        new_roles = Role.query.filter(Role.name.in_(new_role_names)).all() if new_role_names else []
        self.roles.extend(new_roles)

        roles_not_added = new_role_names - {role.name for role in new_roles}
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
            role (str): The name of the Role.

        Returns:
            True if the User has the Role, False otherwise.
        """
        return role in [role.name for role in self.roles]

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


class Role(db.Model, TrackModificationsMixIn):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    resources = db.relationship('Resource', backref=db.backref('role'), cascade='all, delete-orphan')

    def __init__(self, name, description='', resources=None):
        """Initializes a Role object. Each user has one or more Roles associated with it, which determines the user's
            permissions.

        Args:
            name (str): The name of the Role.
            description (str, optional): A description of the role.
            resources (list(dict[name:resource, permissions:list[permission])): A list of dictionaries containing the
                name of the resource, and a list of permission names associated with the resource. Defaults to None.
        """
        self.name = name
        self.description = description
        self.resources = []
        if resources:
            self.set_resources(resources)

    def set_resources(self, new_resources):
        """Adds the given list of resources to the Role object.

        Args:
            new_resources (list(dict[name:resource, permissions:list[permission])): A list of dictionaries containing
                the name of the resource, and a list of permission names associated with the resource.
        """
        new_resource_names = set([resource['name'] for resource in new_resources])
        current_resource_names = set([resource.name for resource in self.resources] if self.resources else [])
        resource_names_to_add = new_resource_names - current_resource_names
        resource_names_to_delete = current_resource_names - new_resource_names
        resource_names_intersect = current_resource_names.intersection(new_resource_names)

        self.resources[:] = [resource for resource in self.resources if resource.name not in resource_names_to_delete]

        for resource_perms in new_resources:
            if resource_perms['name'] in resource_names_to_add:
                self.resources.append(Resource(resource_perms['name'], resource_perms['permissions']))
            elif resource_perms['name'] in resource_names_intersect:
                resource = Resource.query.filter_by(role_id=self.id, name=resource_perms['name']).first()
                if resource:
                    resource.set_permissions(resource_perms['permissions'])
        db.session.commit()

    def as_json(self, with_users=False):
        """Returns the dictionary representation of the Role object.

        Args:
            with_users (bool, optional): Boolean to determine whether or not to include User objects associated with the
                Role in the JSON representation. Defaults to False.

        Returns:
            The dictionary representation of the Role object.
        """
        out = {"id": self.id,
               "name": self.name,
               "description": self.description,
               "resources": [resource.as_json() for resource in self.resources]}
        if with_users:
            out['users'] = [user.username for user in self.users]
        return out


class Resource(db.Model, TrackModificationsMixIn):
    __tablename__ = 'resource'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    permissions = db.relationship('Permission', backref=db.backref('resource'), cascade='all, delete-orphan')

    def __init__(self, name, permissions):
        """Initializes a new Resource object, which is a type of Resource that a Role may have access to.

        Args:
            name (str): Name of the Resource object.
            permissions (list[str]): List of permissions ("create", "read", "update", "delete", "execute")
                for the Resource
        """
        self.name = name
        self.set_permissions(permissions)

    def set_permissions(self, new_permissions):
        """Adds the given list of permissions to the Resource object.

        Args:
            new_permissions (list|set[str]): A list of permission names with which the Resource will be associated.
                These permissions must be in the set ["create", "read", "update", "delete", "execute"].
        """
        self.permissions = []
        new_permission_names = set(new_permissions)
        self.permissions.extend([Permission(permission) for permission in new_permission_names])

    def as_json(self, with_roles=False):
        """Returns the dictionary representation of the Resource object.

        Args:
            with_roles (bool, optional): Boolean to determine whether or not to include Role objects associated with the
                Resource in the JSON representation. Defaults to False.
        """
        out = {'id': self.id, 'name': self.name, 'permissions': [permission.name for permission in self.permissions]}
        if with_roles:
            out["role"] = self.role.name
        return out


class Permission(db.Model):
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'))

    def __init__(self, name):
        self.name = name


def add_user(username, password, roles=None):
    """Adds a User object.

    Args:
        username (str): The username for the User.
        password (str): The password for the User.
        roles (list[str]): A list of roles for the User.

    Returns:
        The new User object if successful, else None.
    """
    if User.query.filter_by(username=username).first() is None:
        user = User(username, password, roles=roles)
        db.session.add(user)
        db.session.commit()
        return user
    else:
        return None


def remove_user(username):
    """Removes the user.

    Args:
        username (str): The username of the User to delete.
    """
    User.query.filter_by(username=username).delete()
