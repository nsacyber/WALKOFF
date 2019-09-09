from datetime import datetime, timedelta
import logging
import os
import sys

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED

from api.fastapi_config import FastApiConfig
from api_gateway.serverdb import User


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=FastApiConfig.JWT_ACCESS_TOKEN_EXPIRES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, FastApiConfig.SECRET_KEY,
                             algorithm=FastApiConfig.ALGORITHM)
    return encoded_jwt


def decode_token(to_decode):
    decoded_jtw = jwt.decode(to_decode, FastApiConfig.SECRET_KEY,
                             algorithm=FastApiConfig.ALGORITHM)
    return decoded_jtw


def jwt_refresh_token_required():
    return True


def create_refresh_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # defaults to 30 days
        expire = datetime.utcnow() + timedelta(days=FastApiConfig.JWT_REFRESH_TOKEN_EXPIRES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, FastApiConfig.SECRET_KEY,
                             algorithm=FastApiConfig.ALGORITHM)
    return encoded_jwt


def get_raw_jwt():
    return True


def get_jwt_identity():
    return True


def jwt_required():
    return True


def decode_token():
    return True


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, FastApiConfig.SECRET_KEY, algorithms=[FastApiConfig.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    user = User.query.filter_by(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class ResourcePermissions:
    def __init__(self, resource, permissions):
        self.resource = resource
        self.permissions = permissions