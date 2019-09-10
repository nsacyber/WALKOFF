from datetime import datetime

from pydantic import BaseModel, UUID4
from sqlalchemy import Column, String, JSON, Integer, DateTime
from api.server.db import Base
from api import fastapi_config


class AuthModel(BaseModel):
    username: str
    password: str


class TokenModel(BaseModel):
    username: str
    password: str


class BlacklistedToken(Base):
    id = Column(Integer, primary_key=True)
    jti = Column(String(36), nullable=False)
    user_identity = Column(String(50), nullable=False)
    expires = Column(DateTime, nullable=False)

    def as_json(self):
        """Get the JSON representation of a BlacklistedToken object.

        Returns:
            (dict): The JSON representation of a BlacklistedToken object.
        """
        return {
            'id': self.id,
            'jti': self.jti,
            'user': self.user_identity,
            'expires': str(self.expires)
        }


def revoke_token(db_session, decoded_token):
    """Adds a new token to the database. It is not revoked when it is added

    Args:
        decoded_token (dict): The decoded token
        :param db_session:
    """
    jti = decoded_token['jti']
    user_identity = decoded_token[fastapi_config.JWT_IDENTITY_CLAIM]
    expires = datetime.fromtimestamp(decoded_token['exp'])

    db_token = BlacklistedToken(
        jti=jti,
        user_identity=user_identity,
        expires=expires
    )
    db_session.add(db_token)
    prune_if_necessary()
    db_session.commit()


def is_token_revoked(decoded_token):
    """Checks if the given token is revoked or not. Because we are adding all the
    tokens that we create into this database, if the token is not present
    in the database we are going to consider it revoked, as we don't know where
    it was created.

    Returns:
        (bool): True if the token is revoked, False otherwise.
    """
    jti = decoded_token['jti']
    token = BlacklistedToken.query.filter_by(jti=jti).first()
    return token is not None


def approve_token(db_session, token_id, user):
    """Approves the given token

    Args:
        token_id (int): The ID of the token
        user (User): The User
    """
    token = BlacklistedToken.query.filter_by(id=token_id, user_identity=user).first()
    if token is not None:
        db_session.remove(token)
        prune_if_necessary()
        db_session.commit()


def prune_if_necessary():
    """Prunes the database if necessary"""
    return True
    # TODO:
    #  if (current_app.running_context.cache.incr("number_of_operations")
    #         >= current_app.config['JWT_BLACKLIST_PRUNE_FREQUENCY']):
    #     prune_database()


def prune_database(db_session):
    """Delete tokens that have expired from the database"""
    now = datetime.now()
    expired = BlacklistedToken.query.filter(BlacklistedToken.expires < now).all()
    for token in expired:
        db_session.delete(token)
    db_session.commit()
    # TODO:
    #  current_app.running_context.cache.set("number_of_operations", 0)
