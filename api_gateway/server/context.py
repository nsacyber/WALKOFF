import logging
import os
import re

from sqlalchemy.exc import OperationalError
from redis import Redis

from common.config import config
import api_gateway.executiondb
import api_gateway.scheduler

logger = logging.getLogger(__name__)


class Context(object):

    def __init__(self, init_all=True, app=None):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        try:
            self.execution_db = api_gateway.executiondb.ExecutionDatabase()
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
            exp = re.compile(r"redis://(.*):(\d+)")
            r = re.match(exp, config.REDIS_URI)

            if not r:
                logger.error(f"REDIS_URI not set correctly, got {config.REDIS_URI} "
                             f"but expected URI of form 'redis://hostname:6379'")
                os._exit(1)

            host = r.group(1)
            try:
                port = r.group(2)
            except IndexError:
                port = 6379

            self.cache = Redis(host=host, port=port)
            self.scheduler = api_gateway.scheduler.Scheduler(app)
