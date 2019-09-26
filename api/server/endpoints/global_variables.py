import logging

from motor.motor_asyncio import AsyncIOMotorCollection
from copy import deepcopy
from uuid import UUID
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from api.server.db.global_variable import GlobalVariable

from api.server.db import get_mongo_c, get_mongo_d
from api.server.security import get_jwt_identity
from api.server.db.permissions import auth_check, default_permissions, creator_only_permissions, AccessLevel
from api.server.utils.problems import UniquenessException
from common.config import config
from common.helpers import fernet_encrypt, fernet_decrypt, validate_uuid

logger = logging.getLogger(__name__)

router = APIRouter()


def global_variable_getter(global_variable, global_col: AsyncIOMotorCollection):
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
async def read_all_globals(request: Request, to_decrypt: str = "false", global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)

    key = config.get_from_file(config.ENCRYPTION_KEY_PATH)
    query = await global_col.find().to_list(None)

    ret = []
    if to_decrypt == "false":
        return query
    else:
        for global_var in query:
            to_read = auth_check(curr_user_id, global_var["id_"], "read", "globals", walkoff_db=walkoff_db)
            if to_read:
                temp_var = deepcopy(global_var)
                temp_var["value"] = fernet_decrypt(key, global_var["value"])
                ret.append(temp_var)

        return ret


@router.get("/{global_var}")
def read_global(request: Request, global_var: UUID, to_decrypt: str = "false", global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)

    global_dict = global_variable_getter(global_var, global_col)
    global_id = global_dict["id_"]

    to_read = auth_check(curr_user_id, global_id, "read", "globals", walkoff_db=walkoff_db)
    if to_read:
        if to_decrypt == "false":
            return global_dict
        else:
            key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
            return fernet_decrypt(key, global_dict['value'])
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.delete("/{global_var}")
def delete_global(request: Request, global_var: UUID, global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)

    global_dict = global_variable_getter(global_var, global_col)
    global_id = global_dict['id_']

    to_delete = auth_check(curr_user_id, global_id, "delete", "globals", walkoff_db=walkoff_db)
    if to_delete:
        await global_col.delete_one(global_dict)
        logger.info(f"Global_variable removed {global_dict['name']}")
        return None, HTTPStatus.NO_CONTENT
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/")
def create_global(request: Request, new_global: GlobalVariable, global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)

    global_dict = dict(new_global)
    permissions = global_dict["permissions"]
    access_level = permissions["access_level"]

    if access_level == AccessLevel.CREATOR_ONLY:
        permissions_model = creator_only_permissions(curr_user_id)
        global_dict["permissions"] = permissions_model
    elif access_level == AccessLevel.EVERYONE:
        permissions_model = default_permissions(curr_user_id, walkoff_db, "global_variables")
        global_dict["permissions"] = permissions_model
    elif access_level == AccessLevel.ROLE_BASED:
        global_dict["permissions"]["creator"] = curr_user_id

    try:
        key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
        global_dict['value'] = fernet_encrypt(key, new_global.value)
        await global_col.insert_one(global_dict)
        return global_dict, HTTPStatus.CREATED
    except IntegrityError:
        UniquenessException("global_variable", "create", global_dict["name"])


@router.put("/{global_var}")
def update_global(request: Request, updated_global: GlobalVariable, global_var: UUID,  global_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    walkoff_db = get_mongo_d(request)
    curr_user_id = get_jwt_identity(request)

    old_global = global_variable_getter(global_var, global_col)
    updated_global_dict = dict(updated_global)
    global_id = old_global["id_"]

    new_permissions = updated_global_dict["permissions"]
    access_level = new_permissions["access_level"]

    to_update = auth_check(curr_user_id, global_id, "update", "global_variables", walkoff_db)
    if to_update:
        if access_level == AccessLevel.CREATOR_ONLY:
            updated_global_dict["permissions"] = creator_only_permissions(curr_user_id)
        elif access_level == AccessLevel.EVERYONE:
            updated_global_dict["permissions"] = default_permissions(curr_user_id, walkoff_db, "global_variables")
        elif access_level == AccessLevel.ROLE_BASED:
            updated_global_dict["permissions"]["creator"] = curr_user_id

        try:
            key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
            updated_global_dict['value'] = fernet_encrypt(key, updated_global_dict['value'])
            r = await global_col.replace_one(old_global, updated_global_dict)
            if r.acknowledged:
                logger.info(f"Updated Global {updated_global.name} ({updated_global.id_})")
                return updated_global_dict
        except (IntegrityError, StatementError):
            raise UniquenessException("global_variable", "update", updated_global["name"])
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
