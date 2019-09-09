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

from api_gateway_new.fastapi_config import FastApiConfig
from api_gateway.serverdb import User


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