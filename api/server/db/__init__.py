# from alembic import command
# from alembic.config import Config
import asyncio
import datetime

from starlette.requests import Request
from marshmallow import pre_load, fields
from marshmallow_sqlalchemy import ModelSchema
from sqlalchemy import create_engine, event, MetaData, Column, DateTime
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database

from api.server.db.resource import Permission, Resource
from api.server.db.role import Role
from api.server.db.user import User
import motor.motor_asyncio
import pymongo

from common.config import config, static
from common.helpers import run_coro_to_complete
from api.server.utils.helpers import format_db_path

default_resource_permissions_internal_user = [
    {"name": "app_apis", "permissions": ["create", "read", "update", "delete"]},
    {"name": "apps", "permissions": ["create", "read", "update", "delete"]},
    {"name": "settings", "permissions": ["read", "update"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["create", "read", "update", "delete"]},
    {"name": "roles", "permissions": ["create", "read", "update", "delete"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["create", "read", "update", "delete"]}
]

default_resource_permissions_super_admin = [
    {"name": "app_apis", "permissions": ["create", "read", "update", "delete"]},
    {"name": "apps", "permissions": ["create", "read", "update", "delete"]},
    {"name": "settings", "permissions": ["read", "update"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["create", "read", "update", "delete"]},
    {"name": "roles", "permissions": ["create", "read", "update", "delete"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["create", "read", "update", "delete"]}
]


default_resource_permissions_admin = [
    {"name": "app_apis", "permissions": ["create", "read", "update", "delete"]},
    {"name": "apps", "permissions": ["create", "read", "update", "delete"]},
    {"name": "settings", "permissions": ["read", "update"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["create", "read", "update", "delete"]},
    {"name": "roles", "permissions": ["create", "read", "update", "delete"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["create", "read", "update", "delete"]}
]

default_resource_permissions_app_developer = [
    {"name": "app_apis", "permissions": ["read"]},
    {"name": "apps", "permissions": ["create", "read", "update", "delete"]},
    {"name": "settings", "permissions": ["read"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["read"]},
    {"name": "roles", "permissions": ["read"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["read"]}
]

default_resource_permissions_workflow_developer = [
    {"name": "app_apis", "permissions": ["read"]},
    {"name": "apps", "permissions": []},
    {"name": "settings", "permissions": ["read"]},
    {"name": "global_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflow_variables", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflows", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "dashboards", "permissions": ["create", "read", "update", "delete"]},
    {"name": "workflowstatus", "permissions": ["read"]},
    {"name": "roles", "permissions": ["read"]},
    {"name": "scheduler", "permissions": ["create", "read", "update", "delete", "execute"]},
    {"name": "users", "permissions": ["read"]}
]

default_resource_permissions_workflow_operator = [
    {"name": "app_apis", "permissions": ["read"]},
    {"name": "apps", "permissions": []},
    {"name": "settings", "permissions": ["read"]},
    {"name": "global_variables", "permissions": ["execute"]},
    {"name": "workflow_variables", "permissions": ["read", "update"]},
    {"name": "workflows", "permissions": ["read", "execute"]},
    {"name": "dashboards", "permissions": ["read", "update"]},
    {"name": "workflowstatus", "permissions": ["read"]},
    {"name": "roles", "permissions": ["read"]},
    {"name": "scheduler", "permissions": ["read"]},
    {"name": "users", "permissions": ["read"]}
]

default_resources = ['app_apis', 'apps', 'settings', 'global_variables', 'workflows', 'roles', 'scheduler', 'users']


Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)


class DBEngine(object):
    """Wrapper for the SQLAlchemy database connection object"""

    def __init__(self):
        # Import all modules here for SQLAlchemy to correctly initialize
        # from api.server.db.appapi import AppApi

        self.engine = create_engine(
            format_db_path(config.DB_TYPE, config.EXECUTION_DB_NAME,
                           config.DB_USERNAME, config.get_from_file(config.POSTGRES_KEY_PATH),
                           config.DB_HOST),
            poolclass=NullPool, isolation_level="AUTOCOMMIT")

        if not database_exists(self.engine.url):
            try:
                create_database(self.engine.url)
            except IntegrityError as e:
                pass

        # self.connection = self.engine.connect()
        # self.transaction = self.connection.begin()
        #
        self.session_maker = sessionmaker(bind=self.engine)
        # self.session = scoped_session(session)
        Base.metadata.bind = self.engine
        Base.metadata.create_all(self.engine)

    def current_timestamp(self):
        return datetime.datetime.now()
        # alembic_cfg = Config(api_gateway.config.Config.ALEMBIC_CONFIG, ini_section="execution",
        #                      attributes={'configure_logger': False})
        # command.stamp(alembic_cfg, "head")


def get_db(request: Request):
    return request.state.db


db = DBEngine()


class TrackModificationsMixIn(Base):
    created_at = Column(DateTime, default=db.current_timestamp())
    modified_at = Column(DateTime, default=db.current_timestamp(), onupdate=db.current_timestamp())

# class BaseSchema(ModelSchema):
#     """
#     Base schema, attaches ExecutionDatabase session to model on load.
#     """
#
#     @pre_load
#     def set_nested_session(self, data):
#         """Allow nested schemas to use the parent schema's session. This is a
#         longstanding bug with marshmallow-sqlalchemy.
#
#         https://github.com/marshmallow-code/marshmallow-sqlalchemy/issues/67
#         https://github.com/marshmallow-code/marshmallow/issues/658#issuecomment-328369199
#         """
#         nested_fields = {k: v for k, v in self.fields.items() if type(v) == fields.Nested}
#         for field in nested_fields.values():
#             field.schema.session = self.session
#
#     def load(self, data, session=None, instance=None, *args, **kwargs):
#         session = db.session_maker
#         # ToDo: Automatically find and use instance if 'id' (or key) is passed
#         return super(BaseSchema, self).load(data, session=session, instance=instance, *args, **kwargs)
#

class MongoEngine(object):
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(username=config.DB_USERNAME,
                                                             password=config.get_from_file(config.MONGO_KEY_PATH),
                                                             host=config.DB_HOST)

    async def init_db(self):
        await self.client.walkoff_db.apps.create_index([("id_", pymongo.ASCENDING),
                                                        ("name", pymongo.ASCENDING)],
                                                       unique=True)

    def collection_from_url(self, path: str):
        resource = path.split("/")[2]
        return self.client.walkoff_db[resource]


def get_mongo_c(request: Request):
    return request.state.mongo_c


mongo = MongoEngine()


def initialize_default_resources_internal_user(db_session: Session):
    """Initializes the default resources for an internal user"""
    internal_user = db_session.query(Role).filter(Role.id == 1).first()
    if not internal_user:
        internal_user = Role("internal_user", description="Placeholder description",
                             resources=default_resource_permissions_internal_user, db_session=db_session)
        db_session.add(internal_user)
    else:
        internal_user.set_resources(default_resource_permissions_internal_user)
    db_session.commit()


def initialize_default_resources_super_admin(db_session: Session):
    """Initializes the default resources for a super admin user"""
    super_admin = db_session.query(Role).filter(Role.id == 2).first()
    if not super_admin:
        super_admin = Role("super_admin", description="Placeholder description",
                           resources=default_resource_permissions_super_admin)
        db_session.add(super_admin)
    else:
        super_admin.set_resources(default_resource_permissions_super_admin)
    db_session.commit()


def initialize_default_resources_admin(db_session: Session):
    """Initializes the default resources for an admin user"""
    admin = db_session.query(Role).filter(Role.id == 3).first()
    if not admin:
        admin = Role("admin", description="Placeholder description", resources=default_resource_permissions_admin, db_session=db_session)
        db_session.add(admin)
    else:
        admin.set_resources(default_resource_permissions_admin)
    db_session.commit()


def initialize_default_resources_app_developer(db_session: Session):
    """Initializes the default resources for an app developer"""
    app_developer = db_session.query(Role).filter(Role.id == 4).first()
    if not app_developer:
        app_developer = Role("app_developer", description="Placeholder description",
                                  resources=default_resource_permissions_app_developer, db_session=db_session)
        db_session.add(app_developer)
    else:
        app_developer.set_resources(default_resource_permissions_app_developer)
    db_session.commit()


def initialize_default_resources_workflow_developer(db_session: Session):
    """Initializes the default resources for a workflow developer"""
    workflow_developer = db_session.query(Role).filter(Role.id == 5).first()
    if not workflow_developer:
        workflow_developer = Role("workflow_developer", description="Placeholder description",
                                  resources=default_resource_permissions_workflow_developer, db_session=db_session)
        db_session.add(workflow_developer)
    else:
        workflow_developer.set_resources(default_resource_permissions_workflow_developer)
    db_session.commit()


def initialize_default_resources_workflow_operator(db_session: Session):
    """Initializes the default resources for a workflow operator"""
    workflow_operator = db_session.query(Role).filter(Role.id == 6).first()
    if not workflow_operator:
        workflow_operator = Role("workflow_operator", description="Placeholder description",
                                 resources=default_resource_permissions_workflow_operator, db_session=db_session)
        db_session.add(workflow_operator)
    else:
        workflow_operator.set_resources(default_resource_permissions_workflow_operator)
    db_session.commit()


def get_roles_by_resource_permission(resource_name: str, resource_permission: str, db_session: Session):
    roles = []
    roles.extend(db_session.query(Role).join(Role.resources).join(Resource.permissions).filter(
        Resource.name == resource_name, Permission.name == resource_permission).all())

    return {role_obj.id for role_obj in roles}


def set_resources_for_role(role_name: str, resources: dict, db_session: Session):
    """Sets the resources a role is allowed to access.

    Args:
        role_name (str): The name of the role.
        resources (dict[resource:list[permission]): A dictionary containing the name of the resource, with the value
                being a list of permission names
    """
    r = db_session.query(Role).filter(Role.name == role_name).first()
    r.set_resources(resources)


def clear_resources_for_role(role_name: str, db_session: Session):
    """Clears all of the resources that a role has access to.

    Args:
        role_name (str): The name of the role.
    """
    r = db_session.query(Role).filter(Role.name == role_name).first()
    r.resources = []
    db_session.commit()


def get_all_available_resource_actions():
    """Gets a list of all of the available resource actions

    Returns:
        (list[dict]): A list of dicts containing the resource name and the actions available for that resource
    """
    resource_actions = []
    for resource_perm in default_resource_permissions_admin:
        resource_actions.append(
            {"name": resource_perm['name'], "actions": resource_perm['permissions']})
    return resource_actions


def add_user(username: str, password: str, db_session: Session, roles: list = None):
    """Adds a User object.

    Args:
        username (str): The username for the User.
        password (str): The password for the User.
        roles (list[int], optional): A list of roles for the User. Defaults to None.

    Returns:
        (User): The new User object if successful, else None.
    """
    if db_session.query(User).filter_by(username=username).first() is None:
        u = User(username, password, roles=roles, db_session=db_session)
        db_session.add(u)
        db_session.commit()
        return u
    else:
        return None


def remove_user(username: str, db_session: Session):
    """Removes the user.

    Args:
        username (str): The username of the User to delete.
    """
    db_session.query(User).filter_by(username=username).delete()