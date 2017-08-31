from passlib.hash import pbkdf2_sha512
from functools import wraps
from flask import Response, current_app, request, _request_ctx_stack, redirect, url_for
from werkzeug.local import LocalProxy
from flask_jwt_extended import (jwt_required, create_access_token, get_jwt_identity, create_refresh_token,
                                current_user, get_current_user, jwt_refresh_token_required, get_jwt_claims)
from flask_jwt_extended.jwt_manager import JWTManager
from server.database import User


jwt = JWTManager()


@jwt.user_claims_loader
def add_claims_to_access_token(username):
    user = User.query.filter_by(email=username).first()
    return {'roles': [role.name for role in user.roles]} if user is not None else {}


def roles_accepted(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            claims = get_jwt_claims()
            if 'roles' in claims and (set(roles) & set(claims['roles'])):
                return fn(*args, **kwargs)
            else:
                return "Unauthorized View", 403

        return decorated_view

    return wrapper


def encrypt_password(password):
    return pbkdf2_sha512.hash(password)


def verify_password(password, hashed_password):
    return pbkdf2_sha512.verify(password, hashed_password)
