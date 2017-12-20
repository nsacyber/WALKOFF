from functools import wraps

from flask import request
from flask_jwt_extended import get_jwt_claims
from flask_jwt_extended.config import config
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_jwt_extended.tokens import decode_jwt
from flask_jwt_extended.view_decorators import _load_user

from server.database import User
from server.extensions import jwt
from server.returncodes import FORBIDDEN_ERROR
import server.database
from server.returncodes import UNAUTHORIZED_ERROR
from server.database.tokens import is_token_revoked
import json
import logging

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
    return json.dumps({'error': 'Token is revoked'}), UNAUTHORIZED_ERROR


def admin_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if user_has_correct_roles({1}, all_required=True):
            return fn(*args, **kwargs)
        else:
            return "Unauthorized View", FORBIDDEN_ERROR

    return wrapper


def permissions_accepted_for_resources(*resource_permissions):
    return _permissions_decorator(resource_permissions, all_required=False)


def permissions_required_for_resources(*resource_permissions):
    return _permissions_decorator(resource_permissions, all_required=True)


def _permissions_decorator(resource_permissions, all_required=False):

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            _roles_accepted = set()
            for resource_permission in resource_permissions:
                _roles_accepted |= server.database.get_roles_by_resource_permissions(resource_permission)
            if user_has_correct_roles(_roles_accepted, all_required=all_required):
                return fn(*args, **kwargs)
            return "Unauthorized View", FORBIDDEN_ERROR

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
    return {'error': 'Token expired'}, UNAUTHORIZED_ERROR


def jwt_required_in_query(query_name):
    def wrapped(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            jwt_data = _decode_jwt_from_query_string(query_name)
            ctx_stack.top.jwt = jwt_data
            _load_user(jwt_data[config.identity_claim])
            return fn(*args, **kwargs)

        return wrapper

    return wrapped


def _decode_jwt_from_query_string(param_name):
    # Verify we have the query string
    token = request.args.get(param_name, None)
    if not token:
        raise NoAuthorizationError("Missing {} query param".format(param_name))

    return decode_jwt(
        encoded_token=token,
        secret=config.decode_key,
        algorithm=config.algorithm,
        csrf=False,
        identity_claim=config.identity_claim
    )


class ResourcePermissions:
    def __init__(self, resource, permissions):
        self.resource = resource
        self.permissions = permissions
