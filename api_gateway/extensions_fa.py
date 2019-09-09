from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from common.config import config
from api_gateway.helpers import format_db_path
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.exc import IntegrityError

# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
#
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
# Base = declarative_base()

Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)

if 'sqlite' in config.DB_TYPE:
    engine = create_engine(format_db_path(config.DB_TYPE, config.EXECUTION_DB_NAME),
                                connect_args={'check_same_thread': False}, poolclass=NullPool)
else:
    engine = create_engine(
        format_db_path(config.DB_TYPE, config.EXECUTION_DB_NAME,
                       config.DB_USERNAME, config.get_from_file(config.POSTGRES_KEY_PATH),
                       config.DB_HOST),
        poolclass=NullPool, isolation_level="AUTOCOMMIT")

    if not database_exists(engine.url):
        try:
            create_database(engine.url)
        except IntegrityError as e:
            pass

connection = engine.connect()
transaction = connection.begin()

session = sessionmaker()
session.configure(bind=engine)
session = scoped_session(session)

Base.metadata.bind = engine
Base.metadata.create_all(engine)