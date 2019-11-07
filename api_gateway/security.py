import json
import logging
from functools import wraps
from http import HTTPStatus

from flask_jwt_extended import get_jwt_claims
from flask_jwt_extended.config import config
from flask_jwt_extended.tokens import decode_jwt

import api_gateway.serverdb
from api_gateway.extensions import jwt
from api_gateway.serverdb import User
from api_gateway.serverdb.tokens import is_token_revoked

try:
    from flask import _app_ctx_stack as ctx_stack
except ImportError:  # pragma: no cover
    from flask import _request_ctx_stack as ctx_stack

logger = logging.getLogger(__name__)


@jwt.token_in_blacklist_loader
def is_token_blacklisted(decoded_token):
    return is_token_revoked(decoded_token)


@jwt.user_claims_loader
def add_claims_to_access_token(user_id):
    user = User.query.filter(User.id == user_id).first()
    return {'roles': [role.id for role in user.roles], 'username': user.username} if user is not None else {}


@jwt.revoked_token_loader
def token_is_revoked_loader():
    return json.dumps({'error': 'Token is revoked'}), HTTPStatus.UNAUTHORIZED


def permissions_accepted_for_resources(*resource_permissions):
    return _permissions_decorator(resource_permissions)


def permissions_required_for_resources(*resource_permissions):
    return _permissions_decorator(resource_permissions, all_required=True)


def _permissions_decorator(resource_permissions, all_required=False):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            _roles_accepted = set()
            for resource_permission in resource_permissions:
                _roles_accepted |= api_gateway.serverdb.get_roles_by_resource_permissions(resource_permission)
            if user_has_correct_roles(_roles_accepted, all_required=all_required):
                return fn(*args, **kwargs)
            return "Unauthorized View", HTTPStatus.FORBIDDEN

        return decorated_view

    return wrapper


def user_has_correct_roles(accepted_roles, all_required=False):
    if not accepted_roles:
        return False
    user_roles = set(get_jwt_claims().get('roles', []))
    if all_required:
        return not accepted_roles - user_roles
    else:
        return any(role in accepted_roles for role in user_roles)


@jwt.expired_token_loader
def expired_token_callback():
    return {'error': 'Token expired'}, HTTPStatus.UNAUTHORIZED


# This function is necessary for connexion update to v2.0
def decode_token(token):
    try:
        return decode_jwt(encoded_token=token, secret=config.decode_key, algorithm=config.algorithm,
                          user_claims_key=config.user_claims_key, identity_claim_key=config.identity_claim_key)
    except:
        return expired_token_callback()


class ResourcePermissions:
    def __init__(self, resource, permissions):
        self.resource = resource
        self.permissions = permissions
