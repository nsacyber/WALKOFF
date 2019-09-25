import base64
import logging

from cryptography.fernet import Fernet
from motor.motor_asyncio import AsyncIOMotorCollection
from sqlalchemy.exc import IntegrityError, StatementError
from copy import deepcopy
from uuid import uuid4
from uuid import UUID
from sqlalchemy.orm import Session
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from api.server.db.global_variable import GlobalVariableTemplate, GlobalVariable

from api.server.db import get_db, get_mongo_c, get_mongo_d
from api.security import get_jwt_identity
from api.server.db.permissions import auth_check, default_permissions, creator_only_permissions, AccessLevel
from api.server.utils.problems import UniquenessException
from common import mongo_helpers
from common.config import config
from common.helpers import fernet_encrypt, fernet_decrypt, validate_uuid

logger = logging.getLogger(__name__)

router = APIRouter()


async def global_variable_getter(global_variable, global_col: AsyncIOMotorCollection):
    if validate_uuid(global_variable):
        return await global_col.find_one({"id_": global_variable}, projection={'_id': False})
    else:
        return await global_col.find_one({"name": global_variable}, projection={'_id': False})


# def global_variable_template_getter(global_template, global_col: AsyncIOMotorCollection):
#     if validate_uuid(global_template):
#         return await global_col.find_one({"id_": global_template}, projection={'_id': False})
#     else:
#         return await global_col.find_one({"name": global_template}, projection={'_id': False})


@router.get("/", status_code=200)
async def read_all_globals(request: Request, to_decrypt: str = "false",
                           global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    key = b'walkoff123456walkoff123456walkof'
    key = base64.b64encode(key)

    #key = config.get_from_file(config.ENCRYPTION_KEY_PATH)
    query = await mongo_helpers.get_all_items(global_col, GlobalVariable)

    ret = []
    if to_decrypt == "false":
        return query
    else:
        for global_var in query:
            to_read = await auth_check(curr_user_id, global_var["id_"], "read", "globals", walkoff_db=walkoff_db)
            if to_read:
                temp_var = deepcopy(global_var)
                temp_var["value"] = fernet_decrypt(key, global_var["value"])
                ret.append(temp_var)

        return ret


@router.get("/{global_var}")
async def read_global(request: Request, global_var: UUID, to_decrypt: str = "false",
                      global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    global_variable = await mongo_helpers.get_item(global_col, GlobalVariable, global_var)
    global_id = global_variable.id_

    to_read = await auth_check(curr_user_id, global_id, "read", "globals", walkoff_db=walkoff_db)
    if to_read:
        if to_decrypt == "false":
            return global_variable
        else:
            key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
            key = b'walkoff123456walkoff123456walkof'
            key = base64.b64encode(key)
            return fernet_decrypt(key, global_variable.value)
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.delete("/{global_var}")
async def delete_global(request: Request, global_var: UUID,
                        global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    global_dict = await global_variable_getter(global_var, global_col)
    global_id = global_dict['id_']

    to_delete = await auth_check(curr_user_id, global_id, "delete", "globals", walkoff_db=walkoff_db)
    if to_delete:
        await global_col.delete_one(global_dict)
        logger.info(f"Global_variable removed {global_dict['name']}")
        return None, HTTPStatus.NO_CONTENT
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/")
async def create_global(request: Request, new_global: GlobalVariable,
                        global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    permissions = new_global.permissions
    access_level = permissions.access_level

    if access_level == AccessLevel.CREATOR_ONLY:
        permissions_model = creator_only_permissions(curr_user_id)
        new_global.permissions = permissions_model
    elif access_level == AccessLevel.EVERYONE:
        permissions_model = default_permissions(curr_user_id, walkoff_db, "global_variables")
        new_global.permissions = permissions_model
    elif access_level == AccessLevel.ROLE_BASED:
        new_global.permissions.creator = curr_user_id

    try:
        # key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
        key = b'walkoff123456walkoff123456walkof'
        key = base64.b64encode(key)
        new_global.value = fernet_encrypt(key, new_global.value)
        return await mongo_helpers.create_item(global_col, GlobalVariable, new_global)
    except IntegrityError:
        UniquenessException("global_variable", "create", new_global.name)


@router.put("/{global_var}")
async def update_global(request: Request, updated_global: GlobalVariable, global_var: UUID,
                        global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = await get_jwt_identity(request)

    old_global = await global_variable_getter(global_var, global_col)
    old_global = GlobalVariable(**old_global)
    global_id = str(old_global.id_)

    new_permissions = updated_global.permissions
    access_level = new_permissions.access_level

    to_update = await auth_check(curr_user_id, global_id, "update", "global_variables", walkoff_db)
    if to_update:
        if access_level == AccessLevel.CREATOR_ONLY:
            updated_global.permissions = creator_only_permissions(curr_user_id)
        elif access_level == AccessLevel.EVERYONE:
            updated_global.permissions = default_permissions(curr_user_id, walkoff_db, "global_variables")
        elif access_level == AccessLevel.ROLE_BASED:
            updated_global.permissions.creator = curr_user_id

        try:
           # key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
            key = b'walkoff123456walkoff123456walkof'
            key = base64.b64encode(key)
            updated_global.value = fernet_encrypt(key, updated_global.value)
            return await mongo_helpers.update_item(global_col, GlobalVariable, global_id, updated_global)
        except (IntegrityError, StatementError):
            raise UniquenessException("global_variable", "update", updated_global.name)
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

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
