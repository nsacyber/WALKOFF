from starlette.requests import Request
from fastapi import APIRouter, Depends
from http import HTTPStatus
import logging

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from api.security import (create_access_token, create_refresh_token, get_jwt_identity,
                          get_raw_jwt, decode_token, verify_jwt_refresh_token_in_request)
from api.fastapi_config import FastApiConfig
from api.server.db import get_mongo_c, get_mongo_d
from api.server.db.user import UserModel
from api.server.db.tokens import revoke_token, AuthModel, TokenModel
from api.server.utils.problems import ProblemException, InvalidInputException

from common import mongo_helpers

token_problem_title = 'Could not grant access token.'

invalid_credentials_problem = ProblemException(
    HTTPStatus.UNAUTHORIZED,
    token_problem_title,
    'Invalid username or password.'
)

user_deactivated_problem = ProblemException(
    HTTPStatus.UNAUTHORIZED,
    token_problem_title,
    'User is deactivated.'
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def _authenticate_and_grant_tokens(request: Request, users_col: AsyncIOMotorCollection, creds: AuthModel, with_refresh=False):
    if not (creds.username and creds.password):
        raise invalid_credentials_problem

    user = await mongo_helpers.get_item(users_col, UserModel, creds.username, raise_exc=False)

    if user is None:
        raise invalid_credentials_problem

    if not user.active:
        raise user_deactivated_problem

    if await user.verify_password(creds.password):
        response = {'access_token': await create_access_token(user=user, fresh=True)}
        if with_refresh:
            response['refresh_token'] = await create_refresh_token(user=user)
        await user.login(request.client.host)
        return response
    else:
        raise invalid_credentials_problem


@router.post("/login")
async def login(creds: AuthModel, request: Request, walkoff_db: AsyncIOMotorCollection = Depends(get_mongo_d)):
    user_col = walkoff_db.users
    return await _authenticate_and_grant_tokens(request=request, users_col=user_col, creds=creds, with_refresh=True)


# def fresh_login(creds: AuthModel, request: Request, users_col: AsyncIOMotorCollection = Depends(get_mongo_c)):
#     return _authenticate_and_grant_tokens(request=request, users_col=users_col, creds=creds)


@router.post("/refresh")
async def refresh(request: Request, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d)):
    user_col = walkoff_db.users

    await verify_jwt_refresh_token_in_request(walkoff_db=walkoff_db, request=request)
    current_user_id = await get_jwt_identity(request)

    user = await mongo_helpers.get_item(user_col, UserModel, current_user_id, raise_exc=False)

    if user is None:
        await revoke_token(decoded_token=await get_raw_jwt(request), walkoff_db=walkoff_db)
        raise ProblemException(
            HTTPStatus.UNAUTHORIZED,
            "Could not grant access token.",
            f"User {current_user_id} from refresh JWT identity could not be found.")
    if user.active:
        return {'access_token': await create_access_token(user=user)}
    else:
        raise user_deactivated_problem


@router.post("/logout")
async def logout(json_in: TokenModel, request: Request, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d)):
    user_col = walkoff_db.users
    data = dict(json_in)
    refresh_token = data.get('refresh_token', None) if data else None
    if refresh_token is None:
        raise ProblemException(HTTPStatus.BAD_REQUEST, 'Could not logout.', 'A refresh token is required to logout.')
    decoded_refresh_token = await decode_token(refresh_token)
    if decoded_refresh_token is None:
        raise ProblemException(HTTPStatus.BAD_REQUEST, 'Could not logout.', 'Invalid refresh token.')

    refresh_token_identity = decoded_refresh_token[FastApiConfig.JWT_IDENTITY_CLAIM]
    user_id = await get_jwt_identity(request)
    if user_id == refresh_token_identity:
        user = await mongo_helpers.get_item(user_col, UserModel, user_id, raise_exc=False)
        if user is not None:
            await user.logout()
        await revoke_token(walkoff_db=walkoff_db, decoded_token=decoded_refresh_token)
        return None
    else:
        raise ProblemException(
            HTTPStatus.BAD_REQUEST,
            'Could not logout.',
            'The identity of the refresh token does not match the identity of the authentication token.')

