import logging
import os
import sys

from fastapi import FastAPI
from pydantic import BaseModel

from api_gateway_new.fastapi_config import FastApiConfig

_app = FastAPI()


class Token(BaseModel):
    access_token: str
    token_type: str


app = _app
