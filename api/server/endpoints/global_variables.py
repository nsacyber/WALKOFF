import base64
import logging
from copy import deepcopy
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection
from starlette.requests import Request

from api.server.db.global_variable import GlobalVariable
from api.server.db.mongo import get_mongo_c, get_mongo_d
from api.server.db.permissions import auth_check, default_permissions, creator_only_permissions, AccessLevel, \
    append_super_and_internal
from api.server.security import get_jwt_identity
from api.server.utils.problems import UniquenessException, UnauthorizedException, DoesNotExistException
from common import async_mongo_helpers as mongo_helpers
from common.config import config
from common.helpers import fernet_encrypt, fernet_decrypt

logger = logging.getLogger("API")

router = APIRouter()


@router.get("/",
            response_model=List[GlobalVariable],
            response_description="List of all Global Variables currently loaded in WALKOFF",
            status_code=200)
async def read_all_globals(request: Request, to_decrypt: str = False,
                           global_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                           page: int = 1):
    """
    Returns a list of all Global Variables currently loaded in WALKOFF.
    Pagination is currently not supported.
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    # Pagination is currently not supported.
    if page > 1:
        return []

    key = config.get_from_file(config.ENCRYPTION_KEY_PATH, mode='rb')
    query = await mongo_helpers.get_all_items(global_col, GlobalVariable)

    ret = []
    if to_decrypt == "false":
        return query
    else:
        for global_var in query:
            to_read = await auth_check(global_var, curr_user_id, "read", walkoff_db)
            if to_read:
                temp_var = deepcopy(global_var)
                temp_var.value = fernet_decrypt(key, global_var.value)
                ret.append(temp_var)

        return ret


@router.get("/{global_var}",
            response_model=str,
            response_description="The requested Global Variable.",
            status_code=200)
async def read_global(request: Request, global_var: UUID, to_decrypt: str = "false",
                      global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Returns the Global Variable for the specified id.
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    global_variable = await mongo_helpers.get_item(global_col, GlobalVariable, global_var)

    to_read = await auth_check(global_variable, curr_user_id, "read", walkoff_db)
    if to_read:
        if to_decrypt == "false":
            return global_variable.value
        else:
            key = config.get_from_file(config.ENCRYPTION_KEY_PATH, mode='rb')
            return fernet_decrypt(key, global_variable.value)
    else:
        raise UnauthorizedException("read data for", "Global Variable", global_variable.name)


@router.delete("/{global_var}",
               response_model=bool,
               response_description="Whether the specified Global Variable was deleted.",
               status_code=200)
async def delete_global(request: Request, global_var: UUID,
                        global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Deletes a specific Global Variable (fetched by id).
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    global_variable = await mongo_helpers.get_item(global_col, GlobalVariable, global_var)
    if not global_variable:
        raise DoesNotExistException("delete", "Global Variable", global_var)
    global_id = global_variable.id_

    to_delete = await auth_check(global_variable, curr_user_id, "delete", walkoff_db)
    if to_delete:
        return await mongo_helpers.delete_item(global_col, GlobalVariable, global_id)
    else:
        raise UnauthorizedException("delete data for", "Global Variable", global_variable.name)


@router.post("/",
             response_model=GlobalVariable,
             response_description="The newly created Global Variable.",
             status_code=201)
async def create_global(request: Request, new_global: GlobalVariable,
                        global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Creates a new Global Variable in WALKOFF and returns it.
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    permissions = new_global.permissions
    access_level = permissions.access_level
    if access_level == AccessLevel.CREATOR_ONLY:
        new_global.permissions = await creator_only_permissions(curr_user_id)
    elif access_level == AccessLevel.EVERYONE:
        new_global.permissions = await default_permissions(curr_user_id, walkoff_db, "global_variables")
    elif access_level == AccessLevel.ROLE_BASED:
        await append_super_and_internal(new_global.permissions)
        new_global.permissions.creator = curr_user_id
    try:
        key = config.get_from_file(config.ENCRYPTION_KEY_PATH, mode='rb')
        new_global.value = fernet_encrypt(key, new_global.value)
        return await mongo_helpers.create_item(global_col, GlobalVariable, new_global)
    except Exception as e:
        logger.info(e)
        raise UniquenessException("global_variable", "create", new_global.name)


@router.put("/{global_var}",
            response_model=GlobalVariable,
            response_description="The newly updated Global Variable.",
            status_code=200)
async def update_global(request: Request, updated_global: GlobalVariable, global_var: UUID,
                        global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Updates a specific Global Variable (fetched by id) and returns it.
    """
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    old_global = await mongo_helpers.get_item(global_col, GlobalVariable, global_var)
    if not old_global:
        raise DoesNotExistException("update", "Global Variable", global_var)
    global_id = old_global.id_

    new_permissions = updated_global.permissions
    access_level = new_permissions.access_level

    to_update = await auth_check(old_global, curr_user_id, "update", walkoff_db)
    if to_update:
        if access_level == AccessLevel.CREATOR_ONLY:
            updated_global.permissions = await creator_only_permissions(curr_user_id)
        elif access_level == AccessLevel.EVERYONE:
            updated_global.permissions = await default_permissions(curr_user_id, walkoff_db, "global_variables")
        elif access_level == AccessLevel.ROLE_BASED:
            await append_super_and_internal(updated_global.permissions)
            updated_global.permissions.creator = curr_user_id

        # try:
        key = config.get_from_file(config.ENCRYPTION_KEY_PATH, mode='rb')
        updated_global.value = fernet_encrypt(key, updated_global.value)
        return await mongo_helpers.update_item(global_col, GlobalVariable, global_id, updated_global)
        # except Exception as e:
        #     logger.info(e)
        #     raise UniquenessException("global_variable", "update", updated_global.name)
    else:
        raise UnauthorizedException("update data for", "Global Variable", old_global.name)

# Templates
#
#
# # @paginate(global_variable_schema)
# @router.get("/templates")
# def read_all_global_templates(db_session: Session = Depends(get_db)):
#     query = db_session.query(GlobalVariableTemplate).order_by(
#         GlobalVariableTemplate.name).all()
#     return query
#
#
# @router.get("/templates/{global_template}")
# def read_global_templates(global_template: UUID, db_session: Session = Depends(get_db)):
#     template = global_variable_template_getter(global_template, db_session=db_session)
#     global_json = global_variable_template_schema.dump(template)
#     return global_json
#
#
# @router.delete("/templates/{global_template}", status_code=204)
# def delete_global_templates(global_template: UUID, db_session: Session = Depends(get_db)):
#     template = global_variable_template_getter(global_template, db_session=db_session)
#     db_session.delete(template)
#     logger.info(f"global_variable_template removed {template.name}")
#     db_session.commit()
#     return None, HTTPStatus.NO_CONTENT
#
#
# @router.post("/templates", status_code=201)
# def create_global_templates(body: GlobalVariableTemplate, db_session: Session = Depends(get_db)):
#     data = await body.get_json()
#
#     try:
#         global_variable_template = global_variable_template_schema.load(data)
#         db_session.add(global_variable_template)
#         db_session.commit()
#         return global_variable_template_schema.dump(global_variable_template)
#     except IntegrityError:
#         db_session.rollback()
#         return unique_constraint_problem("global_variable_template", "create", data["name"])
#
#
# @router.put("/templates/{global_template}")
# def update_global_templates(body: GlobalVariableTemplate, global_template, db_session: Session = Depends(get_db)):
#     template = global_variable_template_getter(global_template, db_session=db_session)
#
#     data = await body.get_json()
#     try:
#         global_variable_template_schema.load(data, instance=template)
#         db_session.commit()
#         return global_variable_template_schema.dump(template)
#     except (IntegrityError, StatementError):
#         db_session.rollback()
#         return unique_constraint_problem("global_variable_template", "update", data["name"])
