import logging

from common.config import config
from api_gateway.helpers import format_db_path

logger = logging.getLogger(__name__)


class FlaskConfig(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = format_db_path(config.DB_TYPE, config.SERVER_DB_NAME,
                                             config.DB_USERNAME, config.get_from_file(config.POSTGRES_KEY_PATH),
                                             config.DB_HOST)

    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['refresh']
    JWT_TOKEN_LOCATION = 'headers'

    JWT_BLACKLIST_PRUNE_FREQUENCY = 1000
    MAX_STREAM_RESULTS_SIZE_KB = 156

    ITEMS_PER_PAGE = 20

    SECRET_KEY = config.get_from_file(config.ENCRYPTION_KEY_PATH)

    # ALEMBIC_CONFIG = join('.', 'alembic.ini')
