from passlib.hash import pbkdf2_sha256
from functools import wraps
from flask import Response, current_app, request, _request_ctx_stack, redirect, url_for
from werkzeug.local import LocalProxy
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, create_refresh_token, current_user, get_current_user
from flask_jwt_extended.jwt_manager import JWTManager
from flask_principal import Identity, Permission, RoleNeed, Principal, identity_changed
from server.database import User


#Java Web Tokens Manager
jwt = JWTManager()
principal = Principal()

auth_token_required = jwt_required

@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return user.display()

@jwt.user_identity_loader
def user_idenity_lookup(user):
    return {"id": user.id, "username": user.email, "roles": [role.name for role in user.roles]}

@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    query = User.query.filter_by(email=identity["username"]).first()
    if query:
        user_id = Identity(identity["username"])
        user_id.provides.add(*[RoleNeed(role) for role in identity["roles"]])
        principal.set_identity(user_id)
        return user_id


@jwt.unauthorized_loader
@jwt.invalid_token_loader
@jwt.expired_token_loader
@jwt.needs_fresh_token_loader
@jwt.revoked_token_loader
@jwt.user_loader_error_loader
@jwt.claims_verification_failed_loader
def _get_unauthorized_response(text="UNAUTHORIZED.", headers=None):
    text = text or ""
    headers = headers or {}
    print("ERROR: ", text, request)
    return Response(text, 401, headers)



def roles_accepted(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            perm = Permission(*[RoleNeed(role) for role in roles])
            if get_current_user().can(perm):
                return fn(*args, **kwargs)
            else:
                return "Unauthorized View", 403

        return decorated_view

    return wrapper

roles_required = roles_accepted

# def roles_required(*roles):
#     def wrapper(fn):
#         @wraps(fn)
#         def decorated_view(*args, **kwargs):
#             perms = [Permission(RoleNeed(role)) for role in roles]
#             for perm in perms:
#                 if not perm.can():
#                     return "Unauthorized View"
#             return fn(*args, **kwargs)
#         return decorated_view
#     return wrapper

def encrypt_password(password):
    try:
        result = pbkdf2_sha256.hash(password)
    except:
        result = pbkdf2_sha256.encrypt(password)
    return result

def verify_password(password1, password2):
    return pbkdf2_sha256.verify(password2, password1)
