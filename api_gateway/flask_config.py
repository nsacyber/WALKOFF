import json
import logging
import logging.config
import os
import warnings
from os.path import isfile, join, abspath

from common.config import Config
from api_gateway.helpers import format_db_path

logger = logging.getLogger(__name__)


class FlaskConfig(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = format_db_path(Config.DB_TYPE, Config.SERVER_DB_NAME,
                                             Config.DB_USERNAME, Config.DB_PASSWORD,
                                             Config.DB_HOST)

    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['refresh']
    JWT_TOKEN_LOCATION = 'headers'

    JWT_BLACKLIST_PRUNE_FREQUENCY = 1000
    MAX_STREAM_RESULTS_SIZE_KB = 156

    ITEMS_PER_PAGE = 20

    SECRET_KEY = "SHORTSTOPKEY"

    ALEMBIC_CONFIG = join('.', 'alembic.ini')
