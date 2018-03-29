import flask_sqlalchemy
from flask_jwt_extended.jwt_manager import JWTManager

db = flask_sqlalchemy.SQLAlchemy()
jwt = JWTManager()
