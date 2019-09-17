import logging

from sqlalchemy.exc import IntegrityError, StatementError
from copy import deepcopy
from uuid import uuid4
from uuid import UUID
from sqlalchemy.orm import Session
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException

from api.server.db.global_variable import GlobalVariableSchema, GlobalVariableTemplateSchema
from api.server.db.global_variable import GlobalVariableTemplate, GlobalVariable
from api.server.db.user import User
from api.server.db import get_db
from api.security import get_jwt_claims
from common.roles_helpers import auth_check, update_permissions, default_permissions, creator_check
from common.config import config
from common.helpers import fernet_encrypt, fernet_decrypt
from api.server.utils import helpers, decorators


logger = logging.getLogger(__name__)

router = APIRouter()


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


# with_global_variable = with_resource_factory("global_variable", global_variable_getter)
global_variable_schema = GlobalVariableSchema()

# with_global_variable_template = with_resource_factory("global_variable_template", global_variable_template_getter)
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


@router.get("/{global_var}")
def read_global(*, global_var: UUID, to_decrypt: str = "false", db_session: Session = Depends(get_db)):
    var = global_variable_getter(global_var, db_session)
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db_session.query(User).filter(User.username == username).first()).id

    global_id = str(var.id_)
    to_read = auth_check(global_id, "read", "global_variables")

    if (var.creator == curr_user_id) or to_read:
        global_json = global_variable_schema.dump(var)

        if to_decrypt == "false":
            return global_json
        else:
            key = config.get_from_file(config.ENCRYPTION_KEY_PATH, 'rb')
            return fernet_decrypt(key, global_json['value'])
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.delete("/{global_var}")
def delete_global(global_var: UUID, db_session: Session = Depends(get_db)):
    var = global_variable_getter(global_var, db_session)
    username = get_jwt_claims().get('username', None)
    curr_user_id = (db_session.query(User).filter(User.username == username).first()).id

    global_id = str(var.id_)
    to_delete = auth_check(global_id, "delete", "global_variables")

    if (var.creator == curr_user_id) or to_delete:
        db_session.delete(var)
        logger.info(f"Global_variable removed {var.name}")
        db_session.commit()
        return None, HTTPStatus.NO_CONTENT
    else:
        return None, HTTPStatus.FORBIDDEN


@router.post("/")
def create_global(body: GlobalVariable, db_session: Session = Depends(get_db)):
    data = dict(body)
    global_id = body.id_
    # data.get('id_', str(uuid4()))

    username = get_jwt_claims().get('username', None)
    curr_user = db_session.query(User).filter(User.username == username).first()
    data.update({'creator': curr_user.id})

    new_permissions = body.permissions

    if body.access_level is not None:
        access_level = body.access_level
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
        data['value'] = fernet_encrypt(key, body.value)
        global_variable = global_variable_schema.load(data)
        db_session.add(global_variable)
        db_session.commit()
        return global_variable_schema.dump(global_variable), HTTPStatus.CREATED
    except IntegrityError:
        db_session.rollback()
        return unique_constraint_problem("global_variable", "create", body.name)


@router.put("/{global_var}")
def update_global(body: GlobalVariable, global_var: UUID, db_session: Session = Depends(get_db)):
    var = global_variable_getter(global_var, db_session)

    username = get_jwt_claims().get('username', None)
    curr_user_id = (db_session.query(User).filter(User.username == username).first()).id

    data = await body.get_json()
    global_id = body.id_

    new_permissions = body.permissions
    access_level = body.access_level

    to_update = auth_check(global_id, "update", "global_variables")
    if (var.creator == curr_user_id) or to_update:
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
            data['value'] = fernet_encrypt(key, body.value)
            global_variable_schema.load(data, instance=var)
            db_session.commit()
            return global_variable_schema.dump(var)
        except (IntegrityError, StatementError):
            db_session.rollback()
            return unique_constraint_problem("global_variable", "update", body.name)
    else:
        return None, HTTPStatus.FORBIDDEN

# Templates


# @paginate(global_variable_schema)
@router.get("/templates")
def read_all_global_templates(db_session: Session = Depends(get_db)):
    query = db_session.query(GlobalVariableTemplate).order_by(
        GlobalVariableTemplate.name).all()
    return query


@router.get("/templates/{global_template}")
def read_global_templates(global_template: UUID, db_session: Session = Depends(get_db)):
    template = global_variable_template_getter(global_template, db_session=db_session)
    global_json = global_variable_template_schema.dump(template)
    return global_json


@router.delete("/templates/{global_template}", status_code=204)
def delete_global_templates(global_template: UUID, db_session: Session = Depends(get_db)):
    template = global_variable_template_getter(global_template, db_session=db_session)
    db_session.delete(template)
    logger.info(f"global_variable_template removed {template.name}")
    db_session.commit()
    return None, HTTPStatus.NO_CONTENT


@router.post("/templates", status_code=201)
def create_global_templates(body: GlobalVariableTemplate, db_session: Session = Depends(get_db)):
    data = await body.get_json()

    try:
        global_variable_template = global_variable_template_schema.load(data)
        db_session.add(global_variable_template)
        db_session.commit()
        return global_variable_template_schema.dump(global_variable_template)
    except IntegrityError:
        db_session.rollback()
        return unique_constraint_problem("global_variable_template", "create", data["name"])


@router.put("/templates/{global_template}")
def update_global_templates(body: GlobalVariableTemplate, global_template, db_session: Session = Depends(get_db)):
    template = global_variable_template_getter(global_template, db_session=db_session)

    data = await body.get_json()
    try:
        global_variable_template_schema.load(data, instance=template)
        db_session.commit()
        return global_variable_template_schema.dump(template)
    except (IntegrityError, StatementError):
        db_session.rollback()
        return unique_constraint_problem("global_variable_template", "update", data["name"])
