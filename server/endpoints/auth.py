from server.security import jwt_refresh_token_required, verify_password, create_access_token, create_refresh_token, get_jwt_identity
from flask import current_app, request
from server.returncodes import *


def _authenticate_and_grant_tokens(json_in, with_refresh=False):
    from server.flaskserver import running_context

    def __func():
        username = json_in.get('username', None)
        password = json_in.get('password', None)
        if not (username and password):
            return {"error": "Invalid username or password"}, UNAUTHORIZED_ERROR

        user = running_context.User.query.filter_by(email=username).first()
        if user is None:
            return {"error": "Invalid username or password"}, UNAUTHORIZED_ERROR
        if verify_password(password, user.password):
            response = {'access_token': create_access_token(identity=username, fresh=True)}
            if with_refresh:
                response['refresh_token'] = create_refresh_token(identity=username)
            return response, SUCCESS
        else:
            return {"error": "Invalid password"}, UNAUTHORIZED_ERROR

    return __func()


def login():
    return _authenticate_and_grant_tokens(request.get_json(), with_refresh=True)


def fresh_login():
    return _authenticate_and_grant_tokens(request.get_json(), with_refresh=False)


@jwt_refresh_token_required
def refresh():
    from server.flaskserver import running_context

    def __func():
        current_user = get_jwt_identity()
        user = running_context.User.query.filter_by(email=current_user).first()
        if user is None:
            return {"error": "Invalid user"}, UNAUTHORIZED_ERROR
        else:
            return {'access_token': create_access_token(identity=current_user, fresh=False)}, SUCCESS

    return __func()