import logging
from typing import Union

from http import HTTPStatus
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorCollection

from api.fastapi_config import FastApiConfig
from api.server.db.user import UserModel
from api.server.db import get_mongo_c
from api.security import get_jwt_identity
from api.server.utils.problems import ProblemException
from common.helpers import validate_uuid


logger = logging.getLogger(__name__)


router = APIRouter()


async def user_getter(user_coll: AsyncIOMotorCollection, user: Union[str, int]) -> UserModel:
    if type(user) is int:
        return await user_coll.find_one({"id_": user}, projection={'_id': False})
    else:
        return await user_coll.find_one({"name": user}, projection={'_id': False})


@router.get("/")
async def read_all_users(user_coll: AsyncIOMotorCollection = Depends(get_mongo_c), page: int = 1):
    # page = request.args.get('page', 1, type=int)
    users = []
    for user in (await user_coll.find().to_list(None)):
        # for user in User.query.paginate(page, FastApiConfig.ITEMS_PER_PAGE, False).items:
        # check for internal user
        if user.id != 1:
            users.append(user.as_json())
    return users


@router.post("/", status_code=201)
async def create_user(*, user_coll: AsyncIOMotorCollection = Depends(get_mongo_c), user: UserModel):
    if not await user_getter(user_coll, user.username):
        # user = add_user(username=user.username, password=user.password, db_session=db_session)

        # if request.roles or request.active
        r = await user_coll.insert_one(dict(user))
        if r.acknowledged:
            result = await user_getter(user_coll, user.id_)
            logger.info(f"Created User {result.username} ({result.id_})")
            return result
        #
        # if user.roles or user.active:
        #     role_update_user_fields(data, user, db_session)
        #
        # logger.info(f'User added: {user.as_json()}')
        # return user.as_json()
    else:
        logger.warning(f'Cannot create user {user.username}. User already exists.')
        return ProblemException(
            HTTPStatus.BAD_REQUEST,
            "Could not create user.",
            f'User with username {user.username} already exists')
#
#
# @router.get("/{user_id}")
# def read_user(user_id: int, db_session: Session = Depends(get_db)):
#     user = userid_getter(db_session=db_session, user_id=user_id)
#     # check for internal user
#     if user.id == 1:
#         return None, HTTPStatus.FORBIDDEN
#     else:
#         return user.as_json()
#
#
# @router.get("/personal_data/{username}")
# def read_personal_user(username: str, request: Request, db_session: Session = Depends(get_db)):
#     user = username_getter(db_session=db_session, username=username)
#     current_id = get_jwt_identity(request)
#     if current_id == user.id:
#         return user.as_json()
#     else:
#         return None, HTTPStatus.FORBIDDEN
#
#
# @router.get("/permissions")
# def list_permissions(request: Request, db_session: Session = Depends(get_db)):
#     current_id = get_jwt_identity(request)
#     current_user = db_session.query(User).filter_by(id=current_id).first()
#     return current_user.permission_json()
#
#
# @router.put("/{user_id}")
# def update_user(user_id: int, body: EditUser, request: Request, db_session: Session = Depends(get_db)):
#     user = userid_getter(db_session=db_session, user_id=user_id)
#     data = dict(body)
#     current_user = get_jwt_identity(request)
#
#     # check for internal user
#     if user.id == 1:
#         return None, HTTPStatus.FORBIDDEN
#
#     if user.id == current_user:
#         # check for super_admin, allows ability to update username/password but not roles/active
#         if user.id == 2:
#             user.set_roles([2])
#             user.active = True
#             return update_user_fields(data, user, db_session)
#         return role_update_user_fields(data, user, db_session, update=True)
#     else:
#         # check for super_admin
#         if user.id == 2:
#             return None, HTTPStatus.FORBIDDEN
#         else:
#             response = role_update_user_fields(data, user, db_session, update=True)
#             if isinstance(response, tuple) and response[1] == HTTPStatus.FORBIDDEN:
#                 logger.error(f"User {current_user} does not have permission to update user {user_id.id}")
#                 return ProblemException(
#                     HTTPStatus.FORBIDDEN,
#                     "User could not be updated.",
#                     f"Current user does not have permission to update user {user.id}.")
#             else:
#                 return response
#
#
# @router.put("/personal_data/{username}")
# def update_personal_user(username: str, body: EditPersonalUser, request: Request, db_session: Session = Depends(get_db)):
#     user = username_getter(db_session=db_session, username=username)
#     data = dict(body)
#     current_user = get_jwt_identity(request)
#
#     # check for internal user
#     if user.id == 1:
#         return ProblemException(
#             HTTPStatus.FORBIDDEN,
#             "Could not update user.",
#             f"Current user does not have permission to update user {user.id}.")
#
#     # check password
#     if user.verify_password(body.old_password):
#         if user.id == current_user:
#             # allow ability to update username/password but not roles/active
#             if user.id == 2:
#                 user.set_roles([2])
#                 user.active = True
#                 return update_user_fields(data, user, db_session)
#             else:
#                 return update_user_fields(data, user, db_session)
#         else:
#             return ProblemException(
#                 HTTPStatus.FORBIDDEN,
#                 "Could not update user.",
#                 f"Current user does not have permission to update user {user.id}.")
#     else:
#         return None, HTTPStatus.FORBIDDEN
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
# @router.delete("/{user_id}")
# def delete_user(user_id: int, request: Request, db_session: Session = Depends(get_db)):
#     user = userid_getter(db_session=db_session, user_id=user_id)
#     if user.id != get_jwt_identity(request) and user.id != 1 and user.id != 2:
#         db_session.delete(user)
#         db_session.commit()
#         logger.info(f"User {user.username} deleted")
#         return None, HTTPStatus.NO_CONTENT
#     else:
#         if user.id == get_jwt_identity(request):
#             logger.error(f"Could not delete user {user.id}. User is current user.")
#             return ProblemException(HTTPStatus.FORBIDDEN, "Could not delete user.",
#                                               'Current user cannot delete self.')
#         if user.id == 2:
#             logger.error(f"Could not delete user {user.username}. "
#                                      f"You do not have permission to delete Super Admin.")
#             return ProblemException(HTTPStatus.FORBIDDEN, "Could not delete user.",
#                                               'A user cannot delete Super Admin.')
#         if user.id == 1:
#             logger.error(f"Could not delete user {user.username}. "
#                                      f"You do not have permission to delete WALKOFF's internal user.")
#             return ProblemException(HTTPStatus.FORBIDDEN, "Could not delete user.",
#                                               "A user cannot delete WALKOFF's internal user.")
