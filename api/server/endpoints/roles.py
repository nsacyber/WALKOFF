from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from starlette.requests import Request
from api.server.utils.problems import ProblemException, DoesNotExistException
from http import HTTPStatus
from api.server.db import get_db
from api.server.db.user_init import clear_resources_for_role, get_all_available_resource_actions
from api.server.db.role import Role, AddRoleModel, RoleModel


def role_getter(db_session: Session, role_id: int):
    role = db_session.query(Role).filter_by(id=role_id).first()
    return role


router = APIRouter()


@router.get("/")
def read_all_roles(db_session: Session = Depends(get_db)):
    roles = []
    for role in db_session.query(Role).all():
        # hides internal and super_admin roles
        if role.id != 1 and role.id != 2:
            roles.append(role.as_json())
    return roles, HTTPStatus.OK


@router.post("/")
def create_role(add_role: AddRoleModel, db_session: Session = Depends(get_db)):
    json_data = dict(add_role)
    if not db_session.query(Role).filter_by(name=json_data['name']).first():
        resources = json_data['resources'] if 'resources' in json_data else []
        if '/roles' in resources:
            resources.remove('/roles')
        role_params = {'name': json_data['name'],
                       'description': json_data['description'] if 'description' in json_data else '',
                       'resources': resources, 'db_session': db_session}
        new_role = Role(**role_params)
        db_session.add(new_role)
        db_session.commit()
        # current_app.logger.info(f"Role added: {role_params}")
        return new_role.as_json(), HTTPStatus.CREATED
    else:
        # current_app.logger.warning(f"Role with name {json_data['name']} already exists")
        return ProblemException(
            HTTPStatus.BAD_REQUEST,
            "Could not create role.",
            f"Role with name {json_data['name']} already exists")


@router.get('/{role_id}')
def read_role(role_id: int, db_session: Session = Depends(get_db)):
    role = role_getter(db_session=db_session, role_id=role_id)
    if role is None:
        return ProblemException(
            HTTPStatus.BAD_REQUEST,
            'Could not logout.',
            'The identity of the refresh token does not match the identity of the authentication token.')
    # check for internal or super_admin
    if role.id != 1 or role.id != 2:
        return role.as_json(), HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@router.put('/{role_id}')
def update_role(role_id: int, updated_role: RoleModel, db_session: Session = Depends(get_db)):
    role = role_getter(db_session=db_session, role_id=role_id)
    if role.id != 1 and role.id != 2:
        json_data = dict(updated_role)
        if 'name' in json_data:
            new_name = json_data['name']
            role_db = db_session.query(Role).filter_by(name=new_name).first()
            if role_db is None or role_db.id == json_data['id']:
                role.name = new_name
        if 'description' in json_data:
            role.description = json_data['description']
        if 'resources' in json_data:
            resources = json_data['resources']
            role.set_resources(resources, db_session)
        db_session.commit()
        # current_app.logger.info(f"Edited role {json_data['id']} to {json_data}")
        return role.as_json(), HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@router.delete('/{role_id}')
def delete_role(role_id: int, db_session: Session = Depends(get_db)):
    role = role_getter(db_session=db_session, role_id=role_id)
    if role.id != 1 or role.id != 2:
        clear_resources_for_role(role_name=role.name, db_session=db_session)
        db_session.delete(role)
        db_session.commit()
        return None, HTTPStatus.NO_CONTENT
    else:
        return None, HTTPStatus.FORBIDDEN


@router.get('/availableresourceactions')
def read_available_resource_actions():
    return get_all_available_resource_actions(), HTTPStatus.OK

