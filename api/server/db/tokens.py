from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from api.server.fastapi_config import FastApiConfig

NUMBER_OF_PRUNE_OPERATIONS = 0


class AuthModel(BaseModel):
    username: str
    password: str


class TokenModel(BaseModel):
    refresh_token: str


class BlacklistedToken(BaseModel):
    __tablename__ = 'tokens'
    jti: str
    user_identity: str
    expires: datetime
    _name_field = "jti"


async def revoke_token(decoded_token: dict, walkoff_db: AsyncIOMotorDatabase):
    """Adds a new token to the database. It is not revoked when it is added
    Args:
        decoded_token (dict): The decoded token
        :param decoded_token:
    """
    token_col = walkoff_db.tokens

    jti = decoded_token['jti']
    user_identity = decoded_token[FastApiConfig.JWT_IDENTITY_CLAIM]
    expires = datetime.fromtimestamp(decoded_token['exp'])

    db_token = {
        "jti": jti,
        "user_identity": user_identity,
        "expires": expires
    }
    await token_col.insert_one(db_token)
    await prune_if_necessary(token_col)


async def is_token_revoked(decoded_token: dict, walkoff_db: AsyncIOMotorDatabase):
    """Checks if the given token is revoked or not. Because we are adding all the
    tokens that we create into this database, if the token is not present
    in the database we are going to consider it revoked, as we don't know where
    it was created.
    Returns:
        (bool): True if the token is revoked, False otherwise.
    """
    token_col = walkoff_db.tokens
    jti = decoded_token['jti']
    token_json = await token_col.find_one({"jti": jti}, projection={'_id': False})
    return token_json is not None


async def prune_if_necessary(walkoff_db: AsyncIOMotorDatabase):
    """Prunes the database if necessary"""
    global NUMBER_OF_PRUNE_OPERATIONS  # ToDo: fix this please
    NUMBER_OF_PRUNE_OPERATIONS += 1
    if NUMBER_OF_PRUNE_OPERATIONS >= FastApiConfig.JWT_BLACKLIST_PRUNE_FREQUENCY:
        await prune_database(walkoff_db)


# todo: fix expires LTE format
async def prune_database(walkoff_db):
    """Delete tokens that have expired from the database"""
    global NUMBER_OF_PRUNE_OPERATIONS
    token_col = walkoff_db.tokens

    now = datetime.now()
    expired = await token_col.find({"expires": {"$lte": now}}, projection={'_id': False})
    for token in expired:
        await token_col.delete(dict(token))
    NUMBER_OF_PRUNE_OPERATIONS = 0
