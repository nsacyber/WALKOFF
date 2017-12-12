from flask import request, current_app
from flask_jwt_extended import (jwt_refresh_token_required, create_access_token, create_refresh_token, get_jwt_identity,
                                get_raw_jwt, jwt_required, decode_token)

from server.database import User, db
from server.returncodes import *
from server.tokens import revoke_token


def _authenticate_and_grant_tokens(json_in, with_refresh=False):
    username = json_in.get('username', None)
    password = json_in.get('password', None)
    if not (username and password):
        return {"error": "Invalid username or password"}, UNAUTHORIZED_ERROR

    user = User.query.filter_by(username=username).first()
    if user is None:
        return {"error": "Invalid username or password"}, UNAUTHORIZED_ERROR
    try:
        password = password.encode('utf-8')
    except UnicodeEncodeError:
        return {"error": "Invalid username or password"}, UNAUTHORIZED_ERROR
    if not user.active:
        return {"error": "User is deactivated"}, UNAUTHORIZED_ERROR
    if user.verify_password(password):
        response = {'access_token': create_access_token(identity=user.id, fresh=True)}
        if with_refresh:
            user.login(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
            db.session.commit()
            response['refresh_token'] = create_refresh_token(identity=user.id)
        return response, OBJECT_CREATED
    else:
        return {"error": "Invalid password"}, UNAUTHORIZED_ERROR


def login():
    return _authenticate_and_grant_tokens(request.get_json(), with_refresh=True)


def fresh_login():
    return _authenticate_and_grant_tokens(request.get_json(), with_refresh=False)


@jwt_refresh_token_required
def refresh():
    current_user_id = get_jwt_identity()
    user = User.query.filter(User.id == current_user_id).first()
    if user is None:
        revoke_token(get_raw_jwt())
        return {"error": "Invalid user"}, UNAUTHORIZED_ERROR
    if user.active:
        return {'access_token': create_access_token(identity=current_user_id, fresh=False)}, OBJECT_CREATED
    else:
        return {"error": "User is deactivated"}, UNAUTHORIZED_ERROR


def logout():
    from server.tokens import revoke_token

    @jwt_required
    def __func():
        refresh_token = request.get_json().get('refresh_token', None)
        if refresh_token is None:
            return {'error': 'refresh token is required to logout'}, BAD_REQUEST
        decoded_refresh_token = decode_token(refresh_token)
        refresh_token_identity = decoded_refresh_token[current_app.config['JWT_IDENTITY_CLAIM']]
        user_id = get_jwt_identity()
        if user_id == refresh_token_identity:
            user = User.query.filter(User.id == user_id).first()
            if user is not None:
                user.logout()
            revoke_token(decode_token(refresh_token))
            return {}, SUCCESS
        else:
            return {'error': 'identity of refresh token does not match identity of auth token'}, BAD_REQUEST

    return __func()
