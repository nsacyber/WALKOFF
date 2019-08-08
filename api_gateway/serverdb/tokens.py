from datetime import datetime

from flask import current_app

from api_gateway.extensions import db


class BlacklistedToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)
    user_identity = db.Column(db.String(50), nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

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


def revoke_token(decoded_token):
    """Adds a new token to the database. It is not revoked when it is added

    Args:
        decoded_token (dict): The decoded token
    """
    jti = decoded_token['jti']
    user_identity = decoded_token[current_app.config['JWT_IDENTITY_CLAIM']]
    expires = datetime.fromtimestamp(decoded_token['exp'])

    db_token = BlacklistedToken(
        jti=jti,
        user_identity=user_identity,
        expires=expires
    )
    db.session.add(db_token)
    prune_if_necessary()
    db.session.commit()


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


def approve_token(token_id, user):
    """Approves the given token

    Args:
        token_id (int): The ID of the token
        user (User): The User
    """
    token = BlacklistedToken.query.filter_by(id=token_id, user_identity=user).first()
    if token is not None:
        db.session.remove(token)
        prune_if_necessary()
        db.session.commit()


def prune_if_necessary():
    """Prunes the database if necessary"""
    if (current_app.running_context.cache.incr("number_of_operations")
            >= current_app.config['JWT_BLACKLIST_PRUNE_FREQUENCY']):
        prune_database()


def prune_database():
    """Delete tokens that have expired from the database"""
    now = datetime.now()
    expired = BlacklistedToken.query.filter(BlacklistedToken.expires < now).all()
    for token in expired:
        db.session.delete(token)
    db.session.commit()
    current_app.running_context.cache.set("number_of_operations", 0)
