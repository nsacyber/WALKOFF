from functools import wraps
from flask_jwt_extended import get_jwt_claims
from flask_jwt_extended.jwt_manager import JWTManager
from server.database import User
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
