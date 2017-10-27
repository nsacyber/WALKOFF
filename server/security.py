from functools import wraps

from flask import request
from flask_jwt_extended import get_jwt_claims
from flask_jwt_extended.config import config
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_jwt_extended.jwt_manager import JWTManager
from flask_jwt_extended.tokens import decode_jwt
from flask_jwt_extended.view_decorators import _load_user

from server.database import User

try:
    from flask import _app_ctx_stack as ctx_stack
except ImportError:  # pragma: no cover
    from flask import _request_ctx_stack as ctx_stack
import server.database
from server.returncodes import UNAUTHORIZED_ERROR
from server.tokens import is_token_revoked
import json
import logging

logger = logging.getLogger(__name__)

jwt = JWTManager()


@jwt.token_in_blacklist_loader
def is_token_blacklisted(decoded_token):
    return is_token_revoked(decoded_token)


@jwt.user_claims_loader
def add_claims_to_access_token(username):
    user = User.query.filter_by(username=username).first()
    return {'roles': [role.name for role in user.roles]} if user is not None else {}


@jwt.revoked_token_loader
def token_is_revoked_loader():
    return json.dumps({'error': 'Token is revoked'}), UNAUTHORIZED_ERROR


def roles_accepted(*roles):
    _roles = set(roles)

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            claims = get_jwt_claims()
            if 'roles' in claims and (_roles & set(claims['roles'])):
                return fn(*args, **kwargs)
            else:
                return "Unauthorized View", 403

        return decorated_view

    return wrapper


def roles_accepted_for_resources(*resources):
    _roles_accepted = set()
    for resource in resources:
        try:
            _roles_accepted |= server.database.resource_roles[resource]
        except KeyError:
            logger.error('Unknown resource {}'.format(resource))

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            claims = get_jwt_claims()
            if 'roles' in claims and (_roles_accepted & set(claims['roles'])):
                return fn(*args, **kwargs)
            else:
                return "Unauthorized View", 403

        return decorated_view

    return wrapper


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
