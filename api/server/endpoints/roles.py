from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from motor.motor_asyncio import AsyncIOMotorCollection

from starlette.requests import Request
from api.server.db import get_mongo_c
from api.server.utils.problems import ProblemException, DoesNotExistException
from http import HTTPStatus
from api.server.db import get_db
from api.server.db.user_init import clear_resources_for_role, get_all_available_resource_actions
from api.server.db.role import Role, AddRoleModel, RoleModel


def role_getter(role_col: AsyncIOMotorCollection, role_id: int):
    return await role_col.find_one({"id": role_id}, projection={'_id': False})


router = APIRouter()


@router.get("/")
def read_all_roles(role_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    ret = []
    for role in (await role_col.find().to_list(None)):
        if role.id != 1 and role.id != 2:
            ret.append(RoleModel(**role))
    return ret


@router.post("/")
def create_role(add_role: AddRoleModel, role_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    json_data = dict(add_role)

    if not role_col.find_one({"name": add_role.name}, projection={'_id': False}):
        resources = add_role.resources if 'resources' in add_role else []
        if '/roles' in resources:
            resources.remove('/roles')

        role_params = {'name': add_role.name,
                       'description': add_role.description if 'description' in add_role else '',
                       'resources': resources}
        new_role = RoleModel(**role_params)
        new_role.set_resources(resources, role_col)
        return new_role
    else:
        # current_app.logger.warning(f"Role with name {json_data['name']} already exists")
        return ProblemException(
            HTTPStatus.BAD_REQUEST,
            "Could not create role.",
            f"Role with name {json_data['name']} already exists")


@router.get('/{role_id}')
def read_role(role_id: int, role_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    role = role_getter(role_col, role_id=role_id)
    if role is None:
        return ProblemException(
            HTTPStatus.BAD_REQUEST,
            'Could not logout.',
            'The identity of the refresh token does not match the identity of the authentication token.')
    # check for internal or super_admin
    if role.id != 1 or role.id != 2:
        return dict(role)
    else:
        return None


@router.put('/{role_id}')
def update_role(role_id: int, updated_role: RoleModel, role_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    role = role_getter(role_col, role_id=role_id)
    if role.id != 1 and role.id != 2:
        if 'name' in updated_role:
            new_name = updated_role.name
            role_db = role_col.find_one({"name": new_name}, projection=False)
            # role_db = db_session.query(Role).filter_by(name=new_name).first()
            if role_db is None or role_db.id == updated_role.id:
                role.name = new_name
        if 'description' in updated_role:
            role.description = update_role.description
        if 'resources' in updated_role:
            resources = update_role.resources
            role.set_resources(resources, role_col)
        # current_app.logger.info(f"Edited role {json_data['id']} to {json_data}")
        return dict(role)
    else:
        return None


@router.delete('/{role_id}')
def delete_role(role_id: int, role_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    role = role_getter(role_col, role_id=role_id)
    if role.id != 1 or role.id != 2:
        r = await role_col.delete_one(role)
        return r
    else:
        return None


@router.get('/availableresourceactions')
def read_available_resource_actions():
    return get_all_available_resource_actions(), HTTPStatus.OK

