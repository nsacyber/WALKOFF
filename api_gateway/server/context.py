import logging
import os

from sqlalchemy.exc import OperationalError

import api_gateway.cache
import api_gateway.config
import api_gateway.executiondb
import api_gateway.scheduler
from api_gateway.config import Config

logger = logging.getLogger(__name__)


class Context(object):

    def __init__(self, init_all=True, app=None):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        try:
            self.execution_db = api_gateway.executiondb.ExecutionDatabase(api_gateway.config.Config.EXECUTION_DB_TYPE,
                                                                          api_gateway.config.Config.EXECUTION_DB_PATH,
                                                                          api_gateway.config.Config.EXECUTION_DB_HOST)
        except OperationalError as e:
            if "password" in str(e):
                logger.error("Incorrect username and/or password for execution database. Please make sure these are "
                             "both set correctly in their respective environment variables and try again."
                             f"Error Message: {str(e)}")
            else:
                logger.error("Error connecting to execution database. Please make sure all database settings are "
                             f"correct and try again. Error Message: {str(e)}")
            os._exit(1)

        if init_all:
            self.cache = api_gateway.cache.RedisCacheAdapter(**api_gateway.config.Config.REDIS_OPTIONS)
            self.scheduler = api_gateway.scheduler.Scheduler(app)
