import flask_sqlalchemy
from sqlalchemy import MetaData
from flask_jwt_extended.jwt_manager import JWTManager

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db = flask_sqlalchemy.SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
jwt = JWTManager()
