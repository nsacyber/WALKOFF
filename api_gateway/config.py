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
    from common.config import config as common_config
    # TODO: Merge triple-play config with this old config and replace the hack below
    common_config = common_config
    # Database types
    WALKOFF_DB_TYPE = 'sqlite'
    EXECUTION_DB_TYPE = 'sqlite'

    WALKOFF_DB_HOST = 'localhost'
    EXECUTION_DB_HOST = 'localhost'

    # PATHS
    DATA_PATH = 'data'

    API_PATH = join("api_gateway", "api")
    REDIS_OPTIONS = {'host': 'localhost', 'port': 6379}

    CLIENT_PATH = join("api_gateway", "client")
    CONFIG_PATH = join(DATA_PATH, 'api_gateway.config')
    DB_PATH = abspath(join(DATA_PATH, 'api_gateway.db'))
    EXECUTION_DB_PATH = abspath(join(DATA_PATH, 'execution.db'))

    LOGGING_CONFIG_PATH = join(DATA_PATH, 'log', 'logging.json')


    # AppConfig
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = format_db_path(WALKOFF_DB_TYPE, DB_PATH, 'WALKOFF_DB_USERNAME', 'WALKOFF_DB_PASSWORD',
                                             WALKOFF_DB_HOST)

    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['refresh']
    JWT_TOKEN_LOCATION = 'headers'

    JWT_BLACKLIST_PRUNE_FREQUENCY = 1000
    MAX_STREAM_RESULTS_SIZE_KB = 156

    ITEMS_PER_PAGE = 20

    EXECUTION_DB_USERNAME = ''
    EXECUTION_DB_PASSWORD = ''

    WALKOFF_DB_USERNAME = ''
    WALKOFF_DB_PASSWORD = ''

    SERVER_PUBLIC_KEY = ''
    SERVER_PRIVATE_KEY = ''
    CLIENT_PUBLIC_KEY = ''
    CLIENT_PRIVATE_KEY = ''

    SECRET_KEY = "SHORTSTOPKEY"

    __passwords = ['EXECUTION_DB_PASSWORD', 'WALKOFF_DB_PASSWORD', 'SERVER_PRIVATE_KEY',
                   'CLIENT_PRIVATE_KEY', 'SERVER_PUBLIC_KEY', 'CLIENT_PUBLIC_KEY', 'SECRET_KEY']

    ALEMBIC_CONFIG = join('.', 'alembic.ini')

    SWAGGER_URL = '/api/docs'

    @classmethod
    def load_config(cls, config_path=None):
        """ Loads Walkoff configuration from JSON file

        Args:
            config_path (str): Optional path to the config. Defaults to the CONFIG_PATH class variable.
        """
        if config_path:
            cls.CONFIG_PATH = config_path
        if cls.CONFIG_PATH:
            try:
                if isfile(cls.CONFIG_PATH):
                    with open(cls.CONFIG_PATH) as config_file:
                        config = json.loads(config_file.read())
                        for key, value in config.items():
                            if value:
                                setattr(cls, key.upper(), value)
                        logger.info(f"Config file loaded: {cls.CONFIG_PATH}.")
                else:
                    logger.info(f"Could not find config file: {cls.CONFIG_PATH}")
            except (IOError, OSError, ValueError):
                logger.warning(f"Could not read config file: {cls.CONFIG_PATH}", exc_info=True)

        cls.SQLALCHEMY_DATABASE_URI = format_db_path(cls.WALKOFF_DB_TYPE, cls.DB_PATH, 'WALKOFF_DB_USERNAME',
                                                     'WALKOFF_DB_PASSWORD', cls.WALKOFF_DB_HOST)

    @classmethod
    def write_values_to_file(cls, keys=None):
        """ Writes the current walkoff configuration to a file"""
        if keys is None:
            keys = [key for key in dir(cls) if not key.startswith('__')]

        output = {}
        for key in keys:
            if key.upper() not in cls.__passwords and hasattr(cls, key.upper()):
                output[key.lower()] = getattr(cls, key.upper())

        with open(cls.CONFIG_PATH, 'w') as config_file:
            config_file.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
            logger.info(f"Wrote config file to: {cls.CONFIG_PATH}")

    @classmethod
    def load_env_vars(cls):
        for field in (field for field in dir(cls) if field.isupper()):
            if field in os.environ:
                var_type = type(getattr(cls, field))
                var = os.environ.get(field)
                if var_type == dict:
                    setattr(cls, field, json.loads(var))
                else:
                    setattr(cls, field, var_type(var))
                logger.info((f"Using environment variable: "
                             f"{field} = {f'{var}' if field not in cls.__passwords else '<hidden>'}"))

        cls.SQLALCHEMY_DATABASE_URI = format_db_path(cls.WALKOFF_DB_TYPE, cls.DB_PATH, 'WALKOFF_DB_USERNAME',
                                                     'WALKOFF_DB_PASSWORD', cls.WALKOFF_DB_HOST)


# TODO: Figure out nice way of ensuring the order of operations for all of the flask app init stuff
Config.load_config()
Config.load_env_vars()
setup_logger()
