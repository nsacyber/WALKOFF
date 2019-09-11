from sqlalchemy.exc import IntegrityError, StatementError
from copy import deepcopy
from uuid import uuid4
from uuid import UUID

# from starlette.requests import Request
# from starlette.responses import Response
from common.config import config
from common.helpers import fernet_encrypt, fernet_decrypt
from api.server.utils import helpers
from api.server.db import get_db
from sqlalchemy.orm import Session

from api_gateway.executiondb.global_variable import (GlobalVariable, GlobalVariableSchema,
                                                      GlobalVariableTemplate, GlobalVariableTemplateSchema)
from api_gateway.serverdb.user import User
from pydantic import BaseModel
from typing import List
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, paginate
from api.server.utils.problem import unique_constraint_problem
from http import HTTPStatus
from common.roles_helpers import auth_check, update_permissions, default_permissions, creator_check
from fastapi import APIRouter, Depends, HTTPException


import logging
logger = logging.getLogger(__name__)

router = APIRouter()


class GlobalVariable(BaseModel):
    id_: UUID = None
    _walkoff_type: str = None
    name: str
    permissions: List[object] = None
    access_level: int = None
    creator: int = None
    value: str
    description: str = None


class GlobalVariableTemplate(BaseModel):
    id_: UUID = None
    _walkoff_type: str = None
    name: str
    schema: object
    description: str = None


def global_variable_getter(global_var, db_session: Session = Depends(get_db)):
    validated_global_var = helpers.validate_uuid(global_var)
    if validated_global_var:
        return db_session.query(GlobalVariable)\
            .filter_by(id_=validated_global_var).first()
    else:
        return db_session.query(GlobalVariable).filter_by(name=global_var).first()


def global_variable_template_getter(global_template, db_session: Session = Depends(get_db)):
    if helpers.validate_uuid(global_template):
        return db_session.query(GlobalVariableTemplate).filter_by(
            id_=global_template).first()
    else:
        return db_session.query(GlobalVariableTemplate).filter_by(
            name=global_template).first()


with_global_variable = with_resource_factory("global_variable", global_variable_getter)
global_variable_schema = GlobalVariableSchema()

with_global_variable_template = with_resource_factory("global_variable_template", global_variable_template_getter)
global_variable_template_schema = GlobalVariableTemplateSchema()


@router.get("/", status_code=200)
async def read_all_globals(to_decrypt: str = "false", db_session: Session = Depends(get_db)):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db_session.query(User).filter(User.username == username).first()).id

    key = config.get_from_file(config.ENCRYPTION_KEY_PATH)
    ret = []
    query = db_session.query(GlobalVariable).order_by(GlobalVariable.name).all()

    if to_decrypt == "false":
        return query
    else:
        for global_var in query:
            to_read = auth_check(str(global_var.id_), "read", "global_variables")
            if (global_var.creator == curr_user_id) or to_read:
                temp_var = deepcopy(global_var)
                temp_var.value = fernet_decrypt(key, global_var.value)
                ret.append(temp_var)

        return ret


@with_global_variable("read", "global_var")
@router.get("/{global_var}")
def read_global(global_var: UUID, to_decrypt: str = "false", db_session: Session = Depends(get_db)):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db_session.query(User).filter(User.username == username).first()).id

    global_id = str(global_var.id_)
    to_read = auth_check(global_id, "read", "global_variables")

    if (global_var.creator == curr_user_id) or to_read:
        global_json = global_variable_schema.dump(global_var)

        if to_decrypt == "false":
            return global_json
        else:
            key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
            return fernet_decrypt(key, global_json['value'])
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@with_global_variable("delete", "global_var")
@router.delete("/{global_var}")
def delete_global(global_var: UUID, db_session: Session = Depends(get_db)):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db_session.query(User).filter(User.username == username).first()).id

    global_id = str(global_var.id_)
    to_delete = auth_check(global_id, "delete", "global_variables")

    if (global_var.creator == curr_user_id) or to_delete:
        db_session.delete(global_var)
        db_session.logger.info(f"Global_variable removed {global_var.name}")
        db_session.commit()
        return None, HTTPStatus.NO_CONTENT
    else:
        return None, HTTPStatus.FORBIDDEN


@permissions_accepted_for_resources(ResourcePermissions("global_variables", ["create"]))
@router.post("/")
def create_global(request: GlobalVariable, db_session: Session = Depends(get_db)):
    data = await request.json()
    global_id = request.id_
    # data.get('id_', str(uuid4()))

    username = get_jwt_claims().get('username', None)
    curr_user = db_session.query(User).filter(User.username == username).first()
    data.update({'creator': curr_user.id})

    new_permissions = request.permissions

    if request.access_level is not None:
        access_level = request.access_level
    else:
        access_level = 1

    # creator only
    if access_level == 0:
        update_permissions("global_variables", global_id,
                           new_permissions=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}],
                           creator=curr_user.id)
    # default permissions
    elif access_level == 1:
        default_permissions("global_variables", global_id, data=data, creator=curr_user.id)
    # user-specified permissions
    elif access_level == 2:
        update_permissions("global_variables", global_id, new_permissions=new_permissions, creator=curr_user.id)

    # if new_permissions:
    #     update_permissions("global_variables", global_id, new_permissions=new_permissions, creator=curr_user.id)
    # else:
    #     default_permissions("global_variables", global_id, data=data, creator=curr_user.id)

    try:
        key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
        data['value'] = fernet_encrypt(key, request.value)
        global_variable = global_variable_schema.load(data)
        db_session.add(global_variable)
        db_session.commit()
        return global_variable_schema.dump(global_variable), HTTPStatus.CREATED
    except IntegrityError:
        db_session.rollback()
        return unique_constraint_problem("global_variable", "create", request.name)


@with_global_variable("update", "global_var")
@router.put("/{global_var}")
def update_global(request: GlobalVariable, global_var: UUID, db_session: Session = Depends(get_db)):
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db_session.query(User).filter(User.username == username).first()).id

    data = await request.get_json()
    global_id = request.id_

    new_permissions = request.permissions
    access_level = request.access_level

    to_update = auth_check(global_id, "update", "global_variables")
    if (global_var.creator == curr_user_id) or to_update:
        if access_level == 0:
            auth_check(global_id, "update", "global_variables",
                       updated_roles=[{"role": 1, "permissions": ["delete", "execute", "read", "update"]}])
        if access_level == 1:
            default_permissions("global_variables", global_id, data=data)
        elif access_level == 2:
            auth_check(global_id, "update", "global_variables", updated_roles=new_permissions)
        # if new_permissions:
        #     auth_check(global_id, "update", "global_variables", updated_roles=new_permissions)
        # else:
        #     default_permissions("global_variables", global_id, data=data)
        try:
            key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
            data['value'] = fernet_encrypt(key, request.value)
            global_variable_schema.load(data, instance=global_var)
            db_session.commit()
            return global_variable_schema.dump(global_var)
        except (IntegrityError, StatementError):
            db_session.rollback()
            return unique_constraint_problem("global_variable", "update", request.name)
    else:
        return None, HTTPStatus.FORBIDDEN

# Templates


@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["read"]))
@paginate(global_variable_schema)
@router.get("/templates")
def read_all_global_templates(db_session: Session = Depends(get_db)):
    query = db_session.query(GlobalVariableTemplate).order_by(
        GlobalVariableTemplate.name).all()
    return query


@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["read"]))
@with_global_variable_template("read", "global_template")
@router.get("/templates/{global_template}")
def read_global_templates(global_template: UUID):
    global_json = global_variable_template_schema.dump(global_template)
    return global_json


@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["delete"]))
@with_global_variable_template("delete", "global_template")
@router.delete("/templates/{global_template}", status_code=204)
def delete_global_templates(global_template: UUID, db_session: Session = Depends(get_db)):
    db_session.delete(global_template)
    db_session.logger.info(f"global_variable_template removed {global_template.name}")
    db_session.commit()
    return None, HTTPStatus.NO_CONTENT


@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["create"]))
@router.post("/templates", status_code=201)
def create_global_templates(request: GlobalVariableTemplate, db_session: Session = Depends(get_db)):
    data = await request.get_json()

    try:
        global_variable_template = global_variable_template_schema.load(data)
        db_session.add(global_variable_template)
        db_session.commit()
        return global_variable_template_schema.dump(global_variable_template)
    except IntegrityError:
        db_session.rollback()
        return unique_constraint_problem("global_variable_template", "create", data["name"])


@permissions_accepted_for_resources(ResourcePermissions("global_variable_templates", ["update"]))
@with_global_variable_template("update", "global_template")
@router.put("/templates/{global_template}")
def update_global_templates(request: GlobalVariableTemplate, global_template, db_session: Session = Depends(get_db)):
    data = await request.get_json()
    try:
        global_variable_template_schema.load(data, instance=global_template)
        db_session.commit()
        return global_variable_template_schema.dump(global_template)
    except (IntegrityError, StatementError):
        db_session.rollback()
        return unique_constraint_problem("global_variable_template", "update", data["name"])
