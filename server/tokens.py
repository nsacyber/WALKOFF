from server.database import db
from datetime import datetime
from flask import current_app


number_of_operations = 0
prune_frequency = 1000


class BlacklistedToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)
    user_identity = db.Column(db.String(50), nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    def as_json(self):
        return {
            'id': self.id,
            'jti': self.jti,
            'user': self.user_identity,
            'expires': self.expires
        }


def revoke_token(decoded_token):
    """
    Adds a new token to the database. It is not revoked when it is added.
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
    """
    Checks if the given token is revoked or not. Because we are adding all the
    tokens that we create into this database, if the token is not present
    in the database we are going to consider it revoked, as we don't know where
    it was created.
    """
    jti = decoded_token['jti']
    token = BlacklistedToken.query.filter_by(jti=jti).first()
    return token is not None


def approve_token(token_id, user):
    """
    Approves the given token.
    """
    token = BlacklistedToken.query.filter_by(id=token_id, user_identity=user).first()
    if token is not None:
        db.session.remove(token)
        prune_if_necessary()
        db.session.commit()


def prune_if_necessary():
    global number_of_operations
    number_of_operations += 1
    if number_of_operations >= prune_frequency:
        prune_database()


def prune_database():
    """
    Delete tokens that have expired from the database.
    """
    now = datetime.now()
    expired = BlacklistedToken.query.filter(BlacklistedToken.expires < now).all()
    for token in expired:
        db.session.delete(token)
    db.session.commit()
