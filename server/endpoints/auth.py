from flask_jwt_extended import (jwt_refresh_token_required, create_access_token, create_refresh_token, get_jwt_identity,
                                get_raw_jwt)
from server.security import verify_password
from flask import request
from server.returncodes import *
from server.tokens import revoke_token
from server.database import User


def _authenticate_and_grant_tokens(json_in, with_refresh=False):
    username = json_in.get('username', None)
    password = json_in.get('password', None)
    if not (username and password):
        return {"error": "Invalid username or password"}, UNAUTHORIZED_ERROR

    user = User.query.filter_by(email=username).first()
    if user is None:
        return {"error": "Invalid username or password"}, UNAUTHORIZED_ERROR
    if verify_password(password, user.password):
        response = {'access_token': create_access_token(identity=username, fresh=True)}
        if with_refresh:
            response['refresh_token'] = create_refresh_token(identity=username)
        return response, OBJECT_CREATED
    else:
        return {"error": "Invalid password"}, UNAUTHORIZED_ERROR


def login():
    return _authenticate_and_grant_tokens(request.get_json(), with_refresh=True)


def fresh_login():
    return _authenticate_and_grant_tokens(request.get_json(), with_refresh=False)


@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    user = User.query.filter_by(email=current_user).first()
    if user is None:
        revoke_token(get_raw_jwt())
        return {"error": "Invalid user"}, UNAUTHORIZED_ERROR
    else:
        return {'access_token': create_access_token(identity=current_user, fresh=False)}, OBJECT_CREATED
