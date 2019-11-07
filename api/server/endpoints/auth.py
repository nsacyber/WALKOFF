import logging
from http import HTTPStatus

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from starlette.requests import Request

from api.server.db.mongo import get_mongo_d
from api.server.db.tokens import revoke_token, AuthModel, TokenModel
from api.server.db.user import UserModel
from api.server.fastapi_config import FastApiConfig
from api.server.security import (create_access_token, create_refresh_token, get_jwt_identity,
                                 get_raw_jwt, decode_token, verify_jwt_refresh_token_in_request,
                                 verify_token_in_decoded, verify_token_not_blacklisted)
from api.server.utils.problems import ProblemException
from common import async_mongo_helpers as mongo_helpers

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
logger = logging.getLogger("API")


@router.post("/login",
             response_model=dict,
             response_description="Login and get access and refresh tokens",
             status_code=HTTPStatus.CREATED)
async def login(*, walkoff_db: AsyncIOMotorCollection = Depends(get_mongo_d),
                creds: AuthModel,
                request: Request):
    """
    Login to WALKOFF using your username and password. Get access and refresh tokens
    """
    user_col = walkoff_db.users
    settings_col = walkoff_db.settings

    if not (creds.username and creds.password):
        raise invalid_credentials_problem

    user = await mongo_helpers.get_item(user_col, UserModel, creds.username, raise_exc=False)

    if user is None:
        raise invalid_credentials_problem

    if not user.active:
        raise user_deactivated_problem

    if await user.verify_password(creds.password):
        response = {'access_token': await create_access_token(settings_col, user=user, fresh=True),
                    'refresh_token': await create_refresh_token(settings_col, user=user)}
        await user.login(request.client.host)
        return response
    else:
        raise invalid_credentials_problem


@router.post("/refresh",
             response_model=dict,
             response_description="Get a fresh access token.")
async def refresh(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                  request: Request):
    """
    Receive a fresh access token.
    """
    user_col = walkoff_db.users
    settings_col = walkoff_db.settings

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
        return {'access_token': await create_access_token(settings_col, user=user)}
    else:
        raise user_deactivated_problem


@router.post("/logout",
             response_model=None,
             response_description="Logout of WALKOFF",
             status_code=204)
async def logout(json_in: TokenModel, request: Request, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d)):
    """
    Using a refresh token, logout of WALKOFF
    """
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
    if str(user_id) == str(refresh_token_identity):
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


@router.post("/verify",
             response_model=bool,
             response_description="Whether the access token is valid.")
async def refresh(*, walkoff_db: AsyncIOMotorDatabase = Depends(get_mongo_d),
                  request: Request):
    """
    Verify the access token's validity
    """
    decoded_token = await get_raw_jwt(request)

    if decoded_token is None:
        e = ProblemException(HTTPStatus.UNAUTHORIZED, "Invalid authorization.",
                             "Access token is expired or missing.")
        return e.as_response()

    await verify_token_in_decoded(decoded_token=decoded_token, request_type='access')
    await verify_token_not_blacklisted(walkoff_db=walkoff_db, decoded_token=decoded_token, request_type='access')

    return True
