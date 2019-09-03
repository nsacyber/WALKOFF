from api_gateway.extensions import db
from api_gateway.serverdb.mixins import TrackModificationsMixIn
from sqlalchemy.types import ARRAY


class Resource(db.Model, TrackModificationsMixIn):
    __tablename__ = 'resource'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    permissions = db.relationship('Permission', backref=db.backref('resource'), cascade='all, delete-orphan')
    operations = db.relationship('Operation', backref=db.backref('resource'), cascade='all, delete-orphan')

    def __init__(self, name, permissions, needed_ids=None):
        """Initializes a new Resource object, which is a type of Resource that a Role may have access to.

        Args:
            name (str): Name of the Resource object.
            permissions (list[str]): List of permissions ("create", "read", "update", "delete", "execute")
                for the Resource
        """
        self.name = name
        self.needed_ids = needed_ids
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
        out = {'id': self.id, 'name': self.name,
               'operations': [(operation.operation_id, operation.permissions_list) for operation in self.operations],
               'permissions': [permission.name for permission in self.permissions]}
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


class Operation(db.Model):
    __tablename__ = 'operation'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operation_id = db.Column(db.String(255), nullable=False)
    permissions_list = db.Column(ARRAY(db.String(255)))
    creator = db.Column(db.Integer)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'))

    def __init__(self, operation_id, permissions_list, creator):
        self.operation_id = operation_id
        self.permissions_list = permissions_list
        self.creator = creator
