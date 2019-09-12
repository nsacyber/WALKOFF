import logging

from http import HTTPStatus
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from starlette.requests import Request

from api.fastapi_config import FastApiConfig
from api.server.db.user import User
from api.server.db.user_init import add_user
from api.server.db import get_db
from api.server.db.user import DisplayUser, EditUser, EditPersonalUser, AddUser
from api.server.utils.problem import Problem
from api.security import get_jwt_identity

logger = logging.getLogger(__name__)


router = APIRouter()


def userid_getter(db_session: Session, user_id: int):
    return db_session.query(User).filter_by(id=user_id).first()


def username_getter(db_session: Session, username: str):
    return db_session.query(User).filter_by(username=username).first()


@router.get("/", response_model=DisplayUser)
def read_all_users(page: int = 1, db_session: Session = Depends(get_db)):
    # page = request.args.get('page', 1, type=int)
    users = []
    for user in db_session.query(User).all():
    # for user in User.query.paginate(page, FastApiConfig.ITEMS_PER_PAGE, False).items:
        # check for internal user
        if user.id != 1:
            users.append(user.as_json())
    return users


@router.post("/", response_model=DisplayUser, status_code=201)
def create_user(body: AddUser, db_session: Session = Depends(get_db)):
    data = dict(body)
    username = body.username
    if not db_session.query(User).filter_by(username=username).first():
        user = add_user(username=username, password=body.password, db_session=db_session)

        # if request.roles or request.active
        if 'roles' in data or 'active' in data:
            role_update_user_fields(data, user, db_session)

        db_session.commit()
        logger.info(f'User added: {user.as_json()}')
        return user.as_json()
    else:
        logger.warning(f'Cannot create user {username}. User already exists.')
        return Problem.from_crud_resource(
            HTTPStatus.BAD_REQUEST,
            'user',
            'create',
            f'User with username {username} already exists')


@router.get("/{user_id}", response_model=DisplayUser)
def read_user(user_id: int, db_session: Session = Depends(get_db)):
    user = userid_getter(db_session=db_session, user_id=user_id)
    # check for internal user
    if user.id == 1:
        return None, HTTPStatus.FORBIDDEN
    else:
        return user.as_json()


@router.get("/personal_data/{username}", response_model=DisplayUser)
def read_personal_user(username: str, request: Request, db_session: Session = Depends(get_db)):
    user = username_getter(db_session=db_session, username=username)
    current_id = get_jwt_identity(request)
    if current_id == user.id:
        return user.as_json()
    else:
        return None, HTTPStatus.FORBIDDEN


@router.get("/permissions", response_model=DisplayUser)
def list_permissions(request: Request, db_session: Session = Depends(get_db)):
    current_id = get_jwt_identity(request)
    current_user = db_session.query(User).filter_by(id=current_id).first()
    return current_user.permission_json()


@router.put("/{user_id}", response_model=DisplayUser)
def update_user(user_id: int, body: EditUser, request: Request, db_session: Session = Depends(get_db)):
    user = userid_getter(db_session=db_session, user_id=user_id)
    data = dict(body)
    current_user = get_jwt_identity(request)

    # check for internal user
    if user.id == 1:
        return None, HTTPStatus.FORBIDDEN

    if user.id == current_user:
        # check for super_admin, allows ability to update username/password but not roles/active
        if user.id == 2:
            user.set_roles([2])
            user.active = True
            return update_user_fields(data, user, db_session)
        return role_update_user_fields(data, user, db_session, update=True)
    else:
        # check for super_admin
        if user.id == 2:
            return None, HTTPStatus.FORBIDDEN
        else:
            response = role_update_user_fields(data, user, db_session, update=True)
            if isinstance(response, tuple) and response[1] == HTTPStatus.FORBIDDEN:
                logger.error(f"User {current_user} does not have permission to update user {user_id.id}")
                return Problem.from_crud_resource(
                    HTTPStatus.FORBIDDEN,
                    'user',
                    'update',
                    f"Current user does not have permission to update user {user.id}.")
            else:
                return response


@router.put("/personal_data/{username}", response_model=DisplayUser)
def update_personal_user(username: str, body: EditPersonalUser, request: Request, db_session: Session = Depends(get_db)):
    user = username_getter(db_session=db_session, username=username)
    data = dict(body)
    current_user = get_jwt_identity(request)

    # check for internal user
    if user.id == 1:
        return Problem.from_crud_resource(
            HTTPStatus.FORBIDDEN,
            'user',
            'update',
            f"Current user does not have permission to update user {user.id}.")

    # check password
    if user.verify_password(body.old_password):
        if user.id == current_user:
            # allow ability to update username/password but not roles/active
            if user.id == 2:
                user.set_roles([2])
                user.active = True
                return update_user_fields(data, user, db_session)
            else:
                return update_user_fields(data, user, db_session)
        else:
            return Problem.from_crud_resource(
                HTTPStatus.FORBIDDEN,
                'user',
                'update',
                f"Current user does not have permission to update user {user.id}.")
    else:
        return None, HTTPStatus.FORBIDDEN


def role_update_user_fields(data, user, db_session, update=False):
    # ensures inability to update roles for super_admin
    if 'roles' in data and user.id != 2:
        user.set_roles([role['id'] for role in data['roles']])
    if 'active' in data and user.id != 2:
        user.active = data['active']
    if update:
        return update_user_fields(data, user, db_session)


def update_user_fields(data, user, db_session):
    if user.id != 1:
        original_username = str(user.username)
        if 'username' in data and data['username']:
            user_db = db_session.query(User).filter_by(username=data['username']).first()
            if user_db is None or user_db.id == user.id:
                user.username = data['username']
            else:
                return Problem(HTTPStatus.BAD_REQUEST, 'Cannot update user.',
                               f"Username {data['username']} is already taken.")
        elif 'new_username' in data and data['new_username']:
            user_db = db_session.query(User).filter_by(username=data['old_username']).first()
            if user_db is None or user_db.id == user.id:
                user.username = data['new_username']
            else:
                return Problem(HTTPStatus.BAD_REQUEST, 'Cannot update user.',
                               f"Username {data['new_username']} is already taken.")
        if 'old_password' in data and 'password' in data and \
                data['old_password'] != "" and data['password'] != "":
            logger.info("go there")
            if user.verify_password(data['old_password']):
                user.password = data['password']
            else:
                user.username = original_username
                return Problem.from_crud_resource(
                    HTTPStatus.UNAUTHORIZED,
                    'user',
                    'update',
                    'Current password is incorrect.')
        db_session.commit()
        logger.info(f"Updated user {user.id}. Updated to: {user.as_json()}")
        return user.as_json(), HTTPStatus.OK
    else:
        return None, HTTPStatus.FORBIDDEN


@router.delete("/{user_id}", response_model=DisplayUser)
def delete_user(user_id: int, request: Request, db_session: Session = Depends(get_db)):
    user = userid_getter(db_session=db_session, user_id=user_id)
    if user.id != get_jwt_identity(request) and user.id != 1 and user.id != 2:
        db_session.delete(user)
        db_session.commit()
        logger.info(f"User {user.username} deleted")
        return None, HTTPStatus.NO_CONTENT
    else:
        if user.id == get_jwt_identity(request):
            logger.error(f"Could not delete user {user.id}. User is current user.")
            return Problem.from_crud_resource(HTTPStatus.FORBIDDEN, 'user', 'delete',
                                              'Current user cannot delete self.')
        if user.id == 2:
            logger.error(f"Could not delete user {user.username}. "
                                     f"You do not have permission to delete Super Admin.")
            return Problem.from_crud_resource(HTTPStatus.FORBIDDEN, 'user', 'delete',
                                              'A user cannot delete Super Admin.')
        if user.id == 1:
            logger.error(f"Could not delete user {user.username}. "
                                     f"You do not have permission to delete WALKOFF's internal user.")
            return Problem.from_crud_resource(HTTPStatus.FORBIDDEN, 'user', 'delete',
                                              "A user cannot delete WALKOFF's internal user.")
