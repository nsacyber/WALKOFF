import flask_sqlalchemy
from sqlalchemy.ext.hybrid import hybrid_property
from passlib.hash import pbkdf2_sha512
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

db = flask_sqlalchemy.SQLAlchemy()

default_resources = ['/', 'playbooks', 'configuration', 'interface', 'trigger', 'metrics', 'users', 'cases', 'apps',
                     'scheduler']

resource_roles = {}


def initialize_resource_roles_from_cleared_database():
    """Initializes the roles dictionary, used in determining which role can access which resource(s).
    """
    for resource in default_resources:
        resource_roles[resource] = {"admin"}


def initialize_resource_roles_from_database():
    for resource in ResourcePermission.query.all():
        resource_roles[resource.resource] = {role.name for role in resource.roles}


def set_resources_for_role(role_name, resources):
    for resource, roles in resource_roles.items():
        if resource in resources:
            roles.add(role_name)
        elif role_name in roles and resource not in resources:
            roles.remove(role_name)
    new_resources = set(resources) - set(resource_roles.keys())
    for new_resource in new_resources:
        resource_roles[new_resource] = {role_name}


def clear_resources_for_role(role_name):
    for resource, roles in resource_roles.items():
        if role_name in roles:
            roles.remove(role_name)

user_roles_association = db.Table('user_roles_association',
                                  db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

roles_resources_association = db.Table('roles_resources_association',
                                       db.Column('resource_permission_id', db.Integer, db.ForeignKey('resource_permission.id')),
                                       db.Column('role_id', db.Integer, db.ForeignKey('role.id')))


class TrackModificationsMixIn(object):
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class User(db.Model, TrackModificationsMixIn):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roles = db.relationship('Role', secondary=user_roles_association,
                            backref=db.backref('users', lazy='dynamic'))
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password = db.Column('password', db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=False)
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    current_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer, default=0)

    def __init__(self, name, password):
        self.username = name
        self._password = pbkdf2_sha512.hash(password)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, new_password):
        self._password = pbkdf2_sha512.hash(new_password)

    def verify_password(self, password_attempt):
        return pbkdf2_sha512.verify(password_attempt, self._password)

    def set_roles(self, new_roles):
        self.roles[:] = []

        new_role_names = set(new_roles)
        new_roles = Role.query.filter(Role.name.in_(new_role_names)).all() if new_role_names else []
        self.roles.extend(new_roles)

        roles_not_added = new_role_names - {role.name for role in new_roles}
        if roles_not_added:
            logger.warning('Cannot add roles {0} to user {1}. Roles do not exist'.format(roles_not_added, self.id))

    def login(self, ip_address):
        self.last_login_at = self.current_login_at
        self.current_login_at = datetime.utcnow()
        self.last_login_ip = self.current_login_ip
        self.current_login_ip = ip_address
        self.login_count += 1
        self.active = True

    def logout(self):
        self.active = False
        if self.login_count > 0:
            self.login_count -= 1
        else:
            logger.warning('User {} logged out, but login count was already at 0'.format(self.id))
        db.session.commit()

    def has_role(self, role):
        return role in [role.name for role in self.roles]

    def as_json(self, with_user_history=False):
        """Returns the dictionary representation of a User object.

        Returns:
            The dictionary representation of a User object.
        """
        out = {"id": self.id,
               "username": self.username,
               "roles": [role.as_json() for role in self.roles]}
        if with_user_history:
            out.update({
                "active": self.active,
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
    resources = db.relationship('ResourcePermission', secondary=roles_resources_association,
                                backref=db.backref('roles', lazy='dynamic'))

    def __init__(self, name, description='', resources=None):
        """Initializes a Role object. Each user has one or more Roles associated with it, which determines the user's
            permissions.

        Args:
            name (str): The name of the Role.
            description (str, optional): A description of the role.
            resources (list[str]): The list of root endpoints that a user with this Role can access.
        """
        self.name = name
        self.description = description
        if resources is not None:
            self.set_resources(resources)

    def set_resources(self, new_resources):
        """Adds the given list of roles to the User object.

        Args:
            new_resources (list|set[str]): A list of resource names with which the Role will be associated.
        """
        self.resources[:] = []
        new_resource_names = set(new_resources)
        new_resources = (ResourcePermission.query.filter(ResourcePermission.resource.in_(new_resource_names)).all()
                         if new_resource_names else [])
        self.resources.extend(new_resources)

        resources_not_added = new_resource_names - {resource.resource for resource in new_resources}
        self.resources.extend([ResourcePermission(resource) for resource in resources_not_added])

    def as_json(self, with_users=False):
        """Returns the dictionary representation of the Role object.

        Returns:
            The dictionary representation of the Role object.
        """
        out = {"id": self.id,
                "name": self.name,
                "description": self.description,
                "resources": [resource.resource for resource in self.resources]}
        if with_users:
            out['users'] = [user.username for user in self.users]
        return out


class ResourcePermission(db.Model):
    __tablename__ = 'resource_permission'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resource = db.Column(db.String(255), unique=True, nullable=False)

    def __init__(self, resource):
        self.resource = resource

    def as_json(self, with_roles=False):
        out = {'resource': self.resource}
        if with_roles:
            out["roles"] = [role.name for role in self.roles]
        return out


def add_user(username, password):
    if User.query.filter_by(username=username).first() is None:
        user = User(username, password)
        db.session.add(user)
        db.session.commit()
        return user
    else:
        return None


def remove_user(username):
    User.query.filter_by(username=username).delete()
