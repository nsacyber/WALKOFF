from datetime import datetime, timedelta
import logging
import os
import sys
import uuid
from functools import wraps
from http import HTTPStatus
import json
from motor.motor_asyncio import AsyncIOMotorDatabase

import jwt
from starlette.requests import Request
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from starlette.status import HTTP_401_UNAUTHORIZED

from api.fastapi_config import FastApiConfig
from api.server.db.tokens import is_token_revoked
from api.server.db.user import UserModel
from api.server.db.role import RoleModel
from api.server.db.resource import ResourceModel
from api.server.db.permissions import PermissionsModel
from api.server.utils.problems import ProblemException

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
logger = logging.getLogger(__name__)


async def verify_jwt_refresh_token_in_request(walkoff_db: AsyncIOMotorDatabase, request: Request):
    decoded_token = await get_raw_jwt(request)
    await verify_token_in_decoded(decoded_token=decoded_token, request_type='refresh')
    await verify_token_not_blacklisted(walkoff_db=walkoff_db, decoded_token=decoded_token, request_type='refresh')
    return True


async def verify_token_in_decoded(decoded_token: dict, request_type: str):
    if decoded_token['type'] != request_type:
        raise ProblemException(HTTPStatus.BAD_REQUEST, "Could not verify token.",
                               'Only {} tokens are allowed'.format(request_type))


async def verify_token_not_blacklisted(walkoff_db: AsyncIOMotorDatabase, decoded_token: dict, request_type: str):
    if not FastApiConfig.JWT_BLACKLIST_ENABLED:
        return
    if request_type == 'access':
        if await is_token_revoked(walkoff_db=walkoff_db, decoded_token=decoded_token):
            raise ProblemException(HTTPStatus.BAD_REQUEST, "Could not verify token.", 'Token has been revoked.')
    if request_type == 'refresh':
        if await is_token_revoked(walkoff_db=walkoff_db, decoded_token=decoded_token):
            raise ProblemException(HTTPStatus.BAD_REQUEST, "Could not verify token.", 'Token has been revoked.')


async def create_access_token(user: UserModel, fresh=False, expires_delta: timedelta = None, user_claims=None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # defaults to 15 minutes
        expire = datetime.utcnow() + timedelta(minutes=FastApiConfig.JWT_ACCESS_TOKEN_EXPIRES)
    if user_claims is None:
        user_claims = await add_claims_to_access_token(user)
    to_encode = {"jti": str(uuid.uuid4()),
                 "exp": expire,
                 "identity": str(user.id_),
                 "fresh": fresh,
                 "type": "access",
                 "user_claims": user_claims}
    encoded_jwt = jwt.encode(to_encode, FastApiConfig.SECRET_KEY, algorithm=FastApiConfig.ALGORITHM)
    return encoded_jwt


async def create_refresh_token(user: UserModel, expires_delta: timedelta = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # defaults to 30 days
        expire = datetime.utcnow() + timedelta(days=FastApiConfig.JWT_REFRESH_TOKEN_EXPIRES)
    to_encode = {"jti": str(uuid.uuid4()),
                 "exp": expire,
                 "identity": str(user.id_),
                 "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, FastApiConfig.SECRET_KEY, algorithm=FastApiConfig.ALGORITHM)
    return encoded_jwt


async def decode_token(to_decode):
    try:
        decoded_jtw = jwt.decode(to_decode, FastApiConfig.SECRET_KEY,
                                 algorithm=FastApiConfig.ALGORITHM)
    except jwt.exceptions.DecodeError:
        return None
    except jwt.exceptions.ExpiredSignatureError:
        return None

    if "user_claims" in decoded_jtw and "roles" in decoded_jtw["user_claims"]:
        decoded_jtw["user_claims"]["roles"] = [uuid.UUID(role) for role in decoded_jtw["user_claims"]["roles"]]

    return decoded_jtw


async def get_raw_jwt(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    jwt_token = auth_header[7:]
    return await decode_token(jwt_token)


async def get_jwt_identity(request: Request):
    rjwt = await get_raw_jwt(request) or {}
    return rjwt.get("identity", "")


async def get_jwt_claims(request: Request):
    rjwt = await get_raw_jwt(request) or {}
    return rjwt.get("user_claims", {})


async def add_claims_to_access_token(user: UserModel):
    return {'roles': [str(role) for role in user.roles], 'username': user.username} if user is not None else {}


async def user_has_correct_roles(accepted_roles, request: Request, all_required=False):
    if not accepted_roles:
        return False
    user_roles = set((await get_jwt_claims(request)).get('roles', []))
    if all_required:
        return not accepted_roles - user_roles
    else:
        return any(role in accepted_roles for role in user_roles)


async def get_roles_by_resource_permission(resource_name: str, resource_permission: str,
                                           walkoff_db: AsyncIOMotorDatabase):
    roles_col = walkoff_db.roles

    all_roles = [RoleModel(**role_json) for role_json in await roles_col.find().to_list(None)]
    accepted_roles = []
    for role in all_roles:
        for resource in role.resources:
            if resource.name == resource_name and resource_permission in resource.permissions:
                accepted_roles.append(role)

    return {role_obj.id_ for role_obj in accepted_roles}
