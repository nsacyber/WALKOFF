import logging
from http import HTTPStatus
from typing import List, Union
from uuid import UUID

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from starlette.requests import Request

from api.server.db.mongo import get_mongo_c, get_mongo_d
from api.server.db.role import RoleModel
from api.server.db.user import UserModel, EditUser, EditPersonalUser
from api.server.db.user_init import DefaultUserUUID as DUsers, DefaultRoleUUID as DRoles, DefaultUserUUID, \
    DefaultRoleUUID
from api.server.security import get_jwt_identity
from api.server.utils.problems import (UnauthorizedException, UniquenessException, InvalidInputException,
                                       DoesNotExistException)
from common import async_mongo_helpers as mongo_helpers

logger = logging.getLogger("API")
router = APIRouter()
ignore_password = {"password": False}

hidden_users = [
    DUsers.INTERNAL_USER.value,
]


@router.get("/", status_code=200,
            response_model=List[UserModel], response_description="List of all users")
async def read_all_users(*, user_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                         page: int = 1,
                         num_per_page: int = 20):
    """
    Returns a list of all Users.
    """
    return await mongo_helpers.get_all_items(user_col, UserModel,
                                             query={"id_": {"$nin": hidden_users}},
                                             projection=ignore_password,
                                             page=page, num_per_page=num_per_page)


@router.get("/{user_id}", status_code=200,
            response_model=UserModel, response_description="The requested User.")
async def read_user(*, user_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                    user_id: Union[UUID, str]):
    """
    Returns the User for the specified username.
    """
    if user_id == "internal_user" or user_id == DefaultUserUUID.INTERNAL_USER.value:
        raise UnauthorizedException("get data for", "User", "internal_user")
    else:
        return await mongo_helpers.get_item(user_col, UserModel, user_id,
                                            query={"id_": {"$nin": hidden_users}},
                                            projection=ignore_password)


@router.post("/", status_code=HTTPStatus.CREATED,
             response_model=UserModel, response_description="The newly created User.")
async def create_user(*, user_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                      new_user: UserModel):
    """
    Creates a new User and returns it.
    """
    if DefaultRoleUUID.INTERNAL_USER.value in new_user.roles or \
            DefaultRoleUUID.SUPER_ADMIN.value in new_user.roles:
        raise UnauthorizedException("create a user with the roles", "User", "internal_user or super_user")
    else:
        return await mongo_helpers.create_item(user_col, UserModel, new_user, projection=ignore_password)


@router.get("/permissions/", status_code=200,
            response_model=List[RoleModel], response_description="List of roles for current user.")
async def list_permissions(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                           with_users: bool = False,
                           request: Request):
    role_col = walkoff_db.roles
    user_col = walkoff_db.users

    current_id = await get_jwt_identity(request)
    current_user = await mongo_helpers.get_item(user_col, UserModel, current_id, raise_exc=False)

    roles = [await mongo_helpers.get_item(role_col, RoleModel, role_id) for role_id in current_user.roles]
    return roles

@router.put("/{user_id}", status_code=200,
            response_model=UserModel, response_description="The newly updated User.")
async def update_user(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                      user_id: Union[UUID, str],
                      new_user: EditUser,
                      request: Request):
    """
    Updates the User for the specified username and returns it.
    """
    user_col = walkoff_db.users
    role_col = walkoff_db.roles

    if user_id == DefaultUserUUID.INTERNAL_USER or user_id == "internal_user":
        raise UnauthorizedException("update", "User", "internal_user")

    user: UserModel = await mongo_helpers.get_item(user_col, UserModel, user_id, raise_exc=False)
    if not user:
        raise DoesNotExistException("update", "User", user_id)

    current_user: UserModel = await mongo_helpers.get_item(user_col, UserModel, await get_jwt_identity(request))
    user_string = f"{user.username} ({user.id_})"

    if await user.verify_password(new_user.old_password):
        if user.id_ == DefaultUserUUID.SUPER_ADMIN.value \
                or DefaultRoleUUID.SUPER_ADMIN.value in user.roles:
            if DRoles.SUPER_ADMIN.value not in current_user.roles:
                raise UnauthorizedException("edit values for", "User", "super_admin")
        else:
            if new_user.roles:
                role_ids = [role.id_ for role in await mongo_helpers.get_all_items(role_col, RoleModel)]
                if set(new_user.roles) <= set(role_ids):
                    user.roles = new_user.roles
                else:
                    invalid_roles = set(role_ids) - set(new_user.roles)
                    raise InvalidInputException("edit roles for", "User", user_string,
                                                errors=f"The following roles do not exist: {invalid_roles}")
            user.active = new_user.active

        if new_user.new_username:
            existing_user = await mongo_helpers.get_item(user_col, UserModel, new_user.new_username, raise_exc=False)
            if existing_user:
                raise UniquenessException("change username for", "User", f"{user_string} -> "
                                                                         f"{new_user.new_username} ({user_id})")
            else:
                user.username = new_user.new_username

        if new_user.new_password:
            await user.hash_and_set_password(new_user.new_password)

        return await mongo_helpers.update_item(user_col, UserModel, user_id, user)
    else:
        raise UnauthorizedException("update the data", "User", f"{new_user.username}")


@router.delete("/{user_id}",  status_code=200,
               response_model=bool,  response_description="Whether or not the user was deleted.")
async def delete_user(*, user_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                      user_id: Union[UUID, str],
                      request: Request):
    user = await mongo_helpers.get_item(user_col, UserModel, user_id, projection=ignore_password, raise_exc=False)
    if not user:
        raise DoesNotExistException("delete", "User", user_id)
    user_string = f"{user.username} ({user.id_})"

    if user.id_ in (DefaultUserUUID.INTERNAL_USER.value, DefaultUserUUID.SUPER_ADMIN.value) \
            or user.id_ == await get_jwt_identity(request) \
            or DefaultRoleUUID.INTERNAL_USER.value in user.roles \
            or DefaultRoleUUID.SUPER_ADMIN.value in user.roles:
        raise UnauthorizedException("delete", "User", user_string)
    else:
        return await mongo_helpers.delete_item(user_col, UserModel, user_id)


@router.get("/personal_data/{username}")
async def read_personal_user(*, username: str, user_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                             request: Request):
    curr_id = await get_jwt_identity(request)
    user_obj = await mongo_helpers.get_item(user_col, UserModel, username, projection=ignore_password)
    if not user_obj:
        raise DoesNotExistException("read personal data", "User", username)

    if str(curr_id) == str(user_obj.id_):
        return user_obj
    else:
        raise UnauthorizedException("view personal data for", "User", user_obj.username)


@router.put("/personal_data/{username}")
async def update_personal_user(*, username: str, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                               request: Request,
                               new_user: EditPersonalUser):
    user_col = walkoff_db.users
    curr_id = await get_jwt_identity(request)
    user_obj = await mongo_helpers.get_item(user_col, UserModel, username, projection=ignore_password)
    if not user_obj:
        raise DoesNotExistException("update personal data", "User", username)

    if str(curr_id) == str(user_obj.id):
        d = dict(new_user)
        d.update({"id_": await get_jwt_identity(request),
                  "roles": [], "hashed": False})

        return await update_user(walkoff_db=walkoff_db, user_id=curr_id,
                                 new_user=EditUser(**d), request=request)
    else:
        raise UnauthorizedException("edit personal data for", "User", user_obj.username)

#
#
# def role_update_user_fields(data, user, db_session, update=False):
#     # ensures inability to update roles for super_admin
#     invalid_roles = [1, 2]
#     if 'roles' in data and user.id not in invalid_roles:
#         user.set_roles([role['id'] for role in data['roles']], db_session)
#     if 'active' in data and user.id not in invalid_roles:
#         user.active = data['active']
#     if update:
#         return update_user_fields(data, user, db_session)
#
#
# def update_user_fields(data, user, db_session):
#     if user.id != 1:
#         original_username = str(user.username)
#         if 'username' in data and data['username']:
#             user_db = db_session.query(User).filter_by(username=data['username']).first()
#             if user_db is None or user_db.id == user.id:
#                 user.username = data['username']
#             else:
#                 return ProblemException(HTTPStatus.BAD_REQUEST, 'Cannot update user.',
#                                f"Username {data['username']} is already taken.")
#         elif 'new_username' in data and data['new_username']:
#             user_db = db_session.query(User).filter_by(username=data['old_username']).first()
#             if user_db is None or user_db.id == user.id:
#                 user.username = data['new_username']
#             else:
#                 return ProblemException(HTTPStatus.BAD_REQUEST, 'Cannot update user.',
#                                f"Username {data['new_username']} is already taken.")
#         if 'old_password' in data and 'password' in data and \
#                 data['old_password'] != "" and data['password'] != "":
#             logger.info("go there")
#             if user.verify_password(data['old_password']):
#                 user.password = data['password']
#             else:
#                 user.username = original_username
#                 return ProblemException(
#                     HTTPStatus.UNAUTHORIZED,
#                     "Could not update user.",
#                     'Current password is incorrect.')
#         db_session.commit()
#         logger.info(f"Updated user {user.id}. Updated to: {user.as_json()}")
#         return user.as_json(), HTTPStatus.OK
#     else:
#         return None, HTTPStatus.FORBIDDEN
#
#
