import logging
from typing import List, Union

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from api.server.db.mongo import get_mongo_c
from api.server.db.role import RoleModel
from api.server.db.user_init import default_resource_permissions_admin, DefaultRoleUUID, DefaultRoleUUIDS
from api.server.utils.problems import (UnauthorizedException, UniquenessException, DoesNotExistException)
from common import async_mongo_helpers as mongo_helpers

logger = logging.getLogger("API")
router = APIRouter()

hidden_roles = [
    DefaultRoleUUID.INTERNAL_USER.value,
]


@router.get("/",
            response_model=List[RoleModel], response_description="List of all roles.")
async def read_all_roles(role_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                         page: int = 1,
                         num_per_page: int = 20):
    """
    Returns a list of all roles.
    """
    return await mongo_helpers.get_all_items(role_col, RoleModel,
                                             query={"id_": {"$nin": hidden_roles}},
                                             page=page, num_per_page=num_per_page)


@router.get('/{role_id}',
            response_model=RoleModel, response_description="The requested Role.")
async def read_role(*, role_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                    role_id: Union[int, str]):
    """
    Returns the Role for the specified role name or ID
    """
    role = await mongo_helpers.get_item(role_col, RoleModel, role_id)
    role_string = f"{role.name} ({role.id_})"
    if role.id_ in hidden_roles:
        raise UnauthorizedException("read", "Role", role_string)
    else:
        return role


@router.post("/",
             response_model=RoleModel, response_description="The newly created Role.", status_code=201)
async def create_role(*, role_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                      new_role: RoleModel):
    """
    Creates a new role and returns it.
    """
    return await mongo_helpers.create_item(role_col, RoleModel, new_role)

    # json_data = dict(add_role)
    #
    # if not role_col.find_one({"name": add_role.name}, projection={'_id': False}):
    #     resources = add_role.resources if 'resources' in add_role else []
    #     if '/roles' in resources:
    #         resources.remove('/roles')
    #
    #     role_params = {'name': add_role.name,
    #                    'description': add_role.description if 'description' in add_role else '',
    #                    'resources': resources}
    #     new_role = RoleModel(**role_params)
    #     new_role.set_resources(resources, role_col)
    #     return new_role
    # else:
    #     # current_app.logger.warning(f"Role with name {json_data['name']} already exists")
    #     return ProblemException(
    #         HTTPStatus.BAD_REQUEST,
    #         "Could not create role.",
    #         f"Role with name {json_data['name']} already exists")


@router.put('/{role_id}',
            response_model=RoleModel, response_description="The newly updated Role")
async def update_role(*, role_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                      role_id: Union[int, str],
                      new_role: RoleModel):
    """
    Updates a role and returns it.
    """
    role: RoleModel = await mongo_helpers.get_item(role_col, RoleModel, role_id, raise_exc=False)
    if not role:
        raise DoesNotExistException("update", "Role", role_id)

    role_string = f"{role.name} ({role.id_})"

    if role.id_ in DefaultRoleUUIDS:
        raise UnauthorizedException("update", "role", role_string)

    if new_role.name:
        existing_user = await mongo_helpers.get_item(role_col, RoleModel, new_role.name, raise_exc=False)
        if existing_user:
            raise UniquenessException("change role for", "Role", f"{role_string} -> "
                                                                 f"{new_role.name} ({role.id_})")
        else:
            role.name = new_role.name

    if new_role.description:
        role.description = new_role.description

    if new_role.resources:
        role.resources = new_role.resources

    return await mongo_helpers.update_item(role_col, RoleModel, role_id, role)

    # role = await role_getter(role_col, role_id=role_id)
    # if role.id_ != 1 and role.id_ != 2:
    #     if 'name' in updated_role:
    #         new_name = updated_role.name
    #         role_db = role_col.find_one({"name": new_name}, projection=False)
    #         # role_db = db_session.query(Role).filter_by(name=new_name).first()
    #         if role_db is None or role_db.id_ == updated_role.id_:
    #             role.name = new_name
    #     if 'description' in updated_role:
    #         role.description = update_role.description
    #     if 'resources' in updated_role:
    #         resources = update_role.resources
    #         role.set_resources(resources, role_col)
    #     # current_app.logger.info(f"Edited role {json_data['id_']} to {json_data}")
    #     return dict(role)
    # else:
    #     return None


@router.delete('/{role_id}',
               response_model=bool,
               response_description="Whether or not the role has been successfully deleted.")
async def delete_role(*, role_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                      role_id: Union[int, str]):
    """
    Deletes a role.
    """
    role = await mongo_helpers.get_item(role_col, RoleModel, role_id, raise_exc=False)
    if not role:
        raise DoesNotExistException("delete", "Role", role_id)
    role_string = f"{role.name} ({role.id_})"

    if role.id_ in DefaultRoleUUIDS:
        raise UnauthorizedException("delete", "role", role_string)
    else:
        return await mongo_helpers.delete_item(role_col, RoleModel, role_id)


@router.get('/availableresourceactions/',
            response_model=list,
            response_description="Returned all available resource actions")
async def read_available_resource_actions():
    resource_actions = []
    for resource_perm in default_resource_permissions_admin:
        resource_actions.append(
            {"name": resource_perm['name'], "actions": resource_perm['permissions']})
    return resource_actions
