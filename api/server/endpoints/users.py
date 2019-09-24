import logging
from http import HTTPStatus
from typing import List, Union

from fastapi import APIRouter, Depends
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from api.server.db import get_mongo_c, get_mongo_d
from api.server.db.user import UserModel, EditUser, EditPersonalUser
from api.server.db.role import DefaultRoles as Roles, RoleModel
from api.server.utils.problems import UnauthorizedException, UniquenessException, InvalidInputException
from api.security import get_jwt_identity
from common import mongo_helpers

logger = logging.getLogger(__name__)
router = APIRouter()
ignore_password = {"password": False}


@router.get("/",
            response_model=List[UserModel], response_description="List of all users")
async def read_all_users(*, user_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
    """
    Returns a list of all Users.
    """
    return await mongo_helpers.get_all_items(user_col, UserModel, projection=ignore_password)


@router.get("/{user_id}",
            response_model=UserModel, response_description="The requested User.")
async def read_user(*, user_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                    user_id: Union[int, str]):
    """
    Returns the User for the specified username.
    """
    return await mongo_helpers.get_item(user_col, UserModel, user_id, projection=ignore_password)


@router.post("/", status_code=HTTPStatus.CREATED,
             response_model=UserModel, response_description="The newly created User.")
async def create_user(*, user_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                      new_user: UserModel):
    """
    Creates a new User and returns it.
    """
    return await mongo_helpers.create_item(user_col, UserModel, new_user, projection=ignore_password)


@router.put("/{user_id}",
            response_model=UserModel, response_description="The newly updated User.")
async def update_user(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                      user_id: Union[int, str],
                      new_user: EditUser,
                      request: Request):
    """
    Updates the User for the specified username and returns it.
    """
    user_col = walkoff_db.users
    role_col = walkoff_db.roles

    user: UserModel = await mongo_helpers.get_item(user_col, UserModel, user_id)
    current_user: UserModel = await mongo_helpers.get_item(user_col, UserModel, await get_jwt_identity(request))
    user_string = f"{user.username} ({user.id_})"

    if user.id_ == Roles.INTERNAL_USER or \
            user.id_ == Roles.SUPER_ADMIN and Roles.SUPER_ADMIN not in current_user.roles:
        raise UnauthorizedException("update", "User", f"{user.username} ({user.id_})")

    if user.id_ == current_user.id_ or Roles.SUPER_ADMIN in current_user.roles or Roles.ADMIN in current_user.roles:
        if Roles.SUPER_ADMIN not in current_user.roles and Roles.ADMIN not in current_user.roles:
            if new_user.roles and set(user.roles) != set(new_user.roles):
                raise UnauthorizedException("edit roles for", "User", user_string)
            elif user.active != new_user.active:
                raise UnauthorizedException("enable/disable", "User", user_string)
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

        if new_user.new_password and await user.verify_password(new_user.old_password):
            await user.hash_and_set_password(new_user.new_password)

    return await mongo_helpers.update_item(user_col, UserModel, user_id, user)


@router.delete("/{user_id}")
async def delete_user(*, user_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                      user_id: Union[int, str],
                      request: Request):
    user = await mongo_helpers.get_item(user_col, UserModel, user_id, projection=ignore_password, raise_exc=False)
    user_string = f"{user.username} ({user.id_})"

    if user.id_ in range(1, 3) or user.id_ == await get_jwt_identity(request):
        raise UnauthorizedException("delete", "User", user_string)
    else:
        return await mongo_helpers.delete_item(user_col, UserModel, user_id)


@router.get("/personal_data/")
async def read_personal_user(*, user_col: AsyncIOMotorCollection = Depends(get_mongo_c),
                             request: Request):
    return await mongo_helpers.get_item(user_col, UserModel, await get_jwt_identity(request),
                                        projection=ignore_password)


@router.put("/personal_data/")
async def update_personal_user(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                               request: Request,
                               new_user: EditPersonalUser):
    d = dict(new_user)
    d.update({"id_": await get_jwt_identity(request),
              "roles": [], "hashed": False})

    return await update_user(walkoff_db=walkoff_db, user_id=await get_jwt_identity(request),
                             new_user=EditUser(**d), request=request)

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
