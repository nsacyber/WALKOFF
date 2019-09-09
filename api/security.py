from datetime import datetime, timedelta
import logging
import os
import sys
import uuid
from functools import wraps
from http import HTTPStatus
import json

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from starlette.status import HTTP_401_UNAUTHORIZED

from api.fastapi_config import FastApiConfig
#from api_gateway.serverdb import User
# from api_gateway.serverdb.tokens import is_token_revoked
# import api_gateway
from api_gateway.serverdb.tokens import is_token_revoked

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

"""
JWT DECORATORS
"""


def jwt_refresh_token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_refresh_token_in_request(kwargs['refresh_token'])
        return fn(*args, **kwargs)

    return wrapper


def verify_jwt_refresh_token_in_request(request):
    decoded_token = get_raw_jwt(request)

    verify_token_in_decoded(decoded_token, request_type='refresh')
    verify_token_not_blacklisted(decoded_token, request_type='refresh')
    return True


def verify_token_in_decoded(decoded_token, request_type):
    if decoded_token['type'] != request_type:
        raise jwt.exceptions.InvalidTokenError('Only {} tokens are allowed'.format(request_type))


def verify_token_not_blacklisted(decoded_token, request_type):
    if not FastApiConfig.JWT_BLACKLIST_ENABLED:
        return
    if request_type == 'access':
        if is_token_blacklisted(decoded_token):
            raise RevokedTokenError('Token has been revoked')
    if request_type == 'refresh':
        if is_token_blacklisted(decoded_token):
            raise RevokedTokenError('Token has been revoked')


def token_is_revoked_loader():
    return json.dumps({'error': 'Token is revoked'}), HTTPStatus.UNAUTHORIZED


def is_token_blacklisted(decoded_token):
    return is_token_revoked(decoded_token)


def expired_token_callback():
    return {'error': 'Token expired'}, HTTPStatus.UNAUTHORIZED



"""
JWT FUNCS
"""


def create_access_token(identity, fresh=False, expires_delta: timedelta = None, user_claims=None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=FastApiConfig.JWT_ACCESS_TOKEN_EXPIRES)
    if user_claims is None:
        user_claims = add_claims_to_access_token(identity)
    to_encode = {"jti": str(uuid.uuid4()),
                 "exp": expire,
                 "identity": identity,
                 "fresh": fresh,
                 "type": "access",
                 "user_claims": user_claims}
    encoded_jwt = jwt.encode(to_encode, FastApiConfig.SECRET_KEY,
                             algorithm=FastApiConfig.ALGORITHM)
    return encoded_jwt


def create_refresh_token(identity, expires_delta: timedelta = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # defaults to 30 days
        expire = datetime.utcnow() + timedelta(days=FastApiConfig.JWT_REFRESH_TOKEN_EXPIRES)
    to_encode = {"jti": str(uuid.uuid4()),
                 "exp": expire,
                 "identity": identity,
                 "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, FastApiConfig.SECRET_KEY,
                             algorithm=FastApiConfig.ALGORITHM)
    return encoded_jwt


def decode_token(to_decode):
    decoded_jtw = jwt.decode(to_decode, FastApiConfig.SECRET_KEY,
                             algorithm=FastApiConfig.ALGORITHM)
    return decoded_jtw


def get_raw_jwt(request):
    auth_header = request.headers['Authorization']
    jwt_token = auth_header[7:]
    return decode_token(jwt_token)


def get_jwt_identity(request):
    return get_raw_jwt(request).get("identity", "")


def get_jwt_claims(request):
    return get_raw_jwt(request).get("user_claims", "")


def add_claims_to_access_token(user_id):
    #user = User.query.filter(User.id == user_id).first()
    user = {"roles": ["admin"], "username": "admin"}
    return user
    #return {'roles': [role.id for role in user.roles], 'username': user.username} if user is not None else {}



# def permissions_accepted_for_resources(*resource_permissions):
#     return _permissions_decorator(resource_permissions)
#
#
# def permissions_required_for_resources(*resource_permissions):
#     return _permissions_decorator(resource_permissions, all_required=True)
#
#
# def _permissions_decorator(resource_permissions, all_required=False):
#     def wrapper(fn):
#         @wraps(fn)
#         def decorated_view(*args, **kwargs):
#             _roles_accepted = set()
#             for resource_permission in resource_permissions:
#                 _roles_accepted |= api_gateway.serverdb.get_roles_by_resource_permissions(resource_permission)
#             if user_has_correct_roles(_roles_accepted, all_required=all_required):
#                 return fn(*args, **kwargs)
#             return "Unauthorized View", HTTPStatus.FORBIDDEN
#
#         return decorated_view
#
#     return wrapper
#
#
# def user_has_correct_roles(accepted_roles, all_required=False):
#     if not accepted_roles:
#         return False
#     user_roles = set(get_jwt_claims().get('roles', []))
#     if all_required:
#         return not accepted_roles - user_roles
#     else:
#         return any(role in accepted_roles for role in user_roles)
#
#
# class ResourcePermissions:
#     def __init__(self, resource, permissions):
#         self.resource = resource
#         self.permissions = permissions
