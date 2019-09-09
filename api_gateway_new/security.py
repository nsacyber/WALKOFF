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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")




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
