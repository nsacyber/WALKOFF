from datetime import datetime, timedelta
import logging
import os
import sys
import uuid
from functools import wraps
from http import HTTPStatus
import json

import jwt
from sqlalchemy.orm import Session
from starlette.requests import Request
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from starlette.status import HTTP_401_UNAUTHORIZED

from api.fastapi_config import FastApiConfig
from api.server.db.tokens import is_token_revoked
from api.server.db.user import User
from api.server.db.role import Role
from api.server.db.resource import Resource, Permission
from api.server.utils.problems import ProblemException

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def verify_jwt_refresh_token_in_request(db_session: Session, request: Request):
    decoded_token = get_raw_jwt(request)

    verify_token_in_decoded(decoded_token=decoded_token, request_type='refresh')
    verify_token_not_blacklisted(db_session=db_session, decoded_token=decoded_token, request_type='refresh')
    return True


def verify_token_in_decoded(decoded_token: dict, request_type: str):
    if decoded_token['type'] != request_type:
        raise ProblemException(HTTPStatus.BAD_REQUEST, "Could not verify token.",'Only {} tokens are allowed'.format(request_type))


def verify_token_not_blacklisted(db_session: Session, decoded_token: dict, request_type: str):
    if not FastApiConfig.JWT_BLACKLIST_ENABLED:
        return
    if request_type == 'access':
        if is_token_revoked(db_session=db_session, decoded_token=decoded_token):
            raise ProblemException(HTTPStatus.BAD_REQUEST, "Could not verify token.", 'Token has been revoked.')
    if request_type == 'refresh':
        if is_token_revoked(db_session=db_session, decoded_token=decoded_token):
            raise ProblemException(HTTPStatus.BAD_REQUEST, "Could not verify token.", 'Token has been revoked.')


def create_access_token(identity: int, db_session: Session, fresh=False, expires_delta: timedelta = None, user_claims=None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # defaults to 15 minutes
        expire = datetime.utcnow() + timedelta(minutes=FastApiConfig.JWT_ACCESS_TOKEN_EXPIRES)
    if user_claims is None:
        user_claims = add_claims_to_access_token(db_session, identity)
    to_encode = {"jti": str(uuid.uuid4()),
                 "exp": expire,
                 "identity": identity,
                 "fresh": fresh,
                 "type": "access",
                 "user_claims": user_claims}
    encoded_jwt = jwt.encode(to_encode, FastApiConfig.SECRET_KEY, algorithm=FastApiConfig.ALGORITHM)
    return encoded_jwt


def create_refresh_token(identity: int, expires_delta: timedelta = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # defaults to 30 days
        expire = datetime.utcnow() + timedelta(days=FastApiConfig.JWT_REFRESH_TOKEN_EXPIRES)
    to_encode = {"jti": str(uuid.uuid4()),
                 "exp": expire,
                 "identity": identity,
                 "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, FastApiConfig.SECRET_KEY, algorithm=FastApiConfig.ALGORITHM)
    return encoded_jwt


def decode_token(to_decode):
    decoded_jtw = jwt.decode(to_decode, FastApiConfig.SECRET_KEY,
                             algorithm=FastApiConfig.ALGORITHM)
    return decoded_jtw


def get_raw_jwt(request: Request):
    auth_header = request.headers['Authorization']
    jwt_token = auth_header[7:]
    return decode_token(jwt_token)


def get_jwt_identity(request: Request):
    return get_raw_jwt(request).get("identity", "")


def get_jwt_claims(request: Request):
    return get_raw_jwt(request).get("user_claims", "")


def add_claims_to_access_token(db_session: Session, user_id):
    user = db_session.query(User).filter(User.id == user_id).first()
    return {'roles': [role.id for role in user.roles], 'username': user.username} if user is not None else {}


def user_has_correct_roles(accepted_roles, request: Request, all_required=False):
    if not accepted_roles:
        return False
    user_roles = set(get_jwt_claims(request).get('roles', []))
    if all_required:
        return not accepted_roles - user_roles
    else:
        return any(role in accepted_roles for role in user_roles)


def get_roles_by_resource_permission(resource_name: str, resource_permission: str, db_session: Session):
    roles = []
    roles.extend(db_session.query(Role).join(Role.resources).join(Resource.permissions).filter(
        Resource.name == resource_name, Permission.name == resource_permission).all())

    return {role_obj.id for role_obj in roles}


class ResourcePermissions:
    def __init__(self, resource, permissions):
        self.resource = resource
        self.permissions = permissions
