from api_gateway.extensions_fa import Base
from api_gateway.serverdb.mixins import TrackModificationsMixIn
from api_gateway.serverdb.resource import Resource
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String


class Role(Base, TrackModificationsMixIn):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(String(255))
    resources = relationship('Resource', back_populates='role')

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
        #Base.SessionLocal.commit() ????
        Base.session.commit()

    def as_json(self, with_users=False):
        """Returns the dictionary representation of the Role object.

        Args:
            with_users (bool, optional): Boolean to determine whether or not to include User objects associated with the
                Role in the JSON representation. Defaults to False.

        Returns:
            (dict): The dictionary representation of the Role object.
        """
        out = {"id": self.id,
               "name": self.name,
               "description": self.description,
               "resources": [resource.as_json() for resource in self.resources]}
        if with_users:
            out['users'] = [user.username for user in self.users]
        return out
