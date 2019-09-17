from starlette.requests import Request
from fastapi import APIRouter, Depends
from http import HTTPStatus
import logging

from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.security import (create_access_token, create_refresh_token, get_jwt_identity,
                          get_raw_jwt, decode_token, verify_jwt_refresh_token_in_request)
from api.fastapi_config import FastApiConfig
from api.server.db.user import User
from api.server.db import get_db
from api.server.db.tokens import revoke_token, AuthModel, TokenModel
from api.server.utils.problems import ProblemException, InvalidInputException

token_problem_title = 'Could not grant access token.'

invalid_credentials_problem = ProblemException(
    HTTPStatus.UNAUTHORIZED,
    token_problem_title,
    'Invalid username or password.'
)

user_deactivated_problem = ProblemException(
    HTTPStatus.UNAUTHORIZED,
    token_problem_title,
    'User is deactivated.'
)

router = APIRouter()
logger = logging.getLogger("API")


def _authenticate_and_grant_tokens(request: Request, db_session: Session, creds: AuthModel, with_refresh=False):
    if not (creds.username and creds.password):
        raise invalid_credentials_problem
    user = db_session.query(User).filter_by(username=creds.username).first()
    if user is None:
        raise invalid_credentials_problem
    try:
        password_b = creds.password.encode('utf-8')
    except UnicodeEncodeError:
        raise invalid_credentials_problem

    if not user.active:
        raise user_deactivated_problem

    if user.verify_password(password_b):
        response = {'access_token': create_access_token(identity=user.id, db_session=db_session, fresh=True)}
        if with_refresh:
            user.login(request.client.host)
            # user.login(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
            db_session.commit()
            response['refresh_token'] = create_refresh_token(identity=user.id)
        print(response)
        return response
    else:
        raise invalid_credentials_problem


@router.post("/login")
def login(creds: AuthModel, request: Request, db_session: Session = Depends(get_db)):
    return _authenticate_and_grant_tokens(request=request, db_session=db_session, creds=creds, with_refresh=True)


def fresh_login(json_in: AuthModel, request: Request, db_session: Session = Depends(get_db)):
    return _authenticate_and_grant_tokens(request=request, db_session=db_session, json_in=dict(json_in))


@router.post("/refresh")
def refresh(request: Request, db_session: Session = Depends(get_db)):
    verify_jwt_refresh_token_in_request(db_session=db_session, request=request)
    current_user_id = get_jwt_identity(request)

    user = db_session.query(User).filter_by(id=current_user_id).first()
    if user is None:
        revoke_token(db_session=db_session, decoded_token=get_raw_jwt(request))
        raise ProblemException(
            HTTPStatus.UNAUTHORIZED,
            "Could not grant access token.",
            f"User {current_user_id} from refresh JWT identity could not be found.")
    if user.active:
        return {'access_token': create_access_token(identity=current_user_id, db_session=db_session)}, HTTPStatus.CREATED
    else:
        raise user_deactivated_problem


@router.post("/logout")
def logout(json_in: TokenModel, request: Request, db_session: Session = Depends(get_db)):
    data = dict(json_in)
    refresh_token = data.get('refresh_token', None) if data else None
    if refresh_token is None:
        raise ProblemException(HTTPStatus.BAD_REQUEST, 'Could not logout.', 'A refresh token is required to logout.')
    decoded_refresh_token = decode_token(refresh_token)
    refresh_token_identity = decoded_refresh_token[FastApiConfig.JWT_IDENTITY_CLAIM]
    user_id = get_jwt_identity(request)
    if user_id == refresh_token_identity:
        user = db_session.query(User).filter(User.id == user_id).first()
        if user is not None:
            user.logout(db_session=db_session)
        revoke_token(db_session=db_session, decoded_token=decode_token(refresh_token))
        return None, HTTPStatus.NO_CONTENT
    else:
        raise ProblemException(
            HTTPStatus.BAD_REQUEST,
            'Could not logout.',
            'The identity of the refresh token does not match the identity of the authentication token.')

