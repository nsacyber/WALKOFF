import logging
import os

from sqlalchemy.exc import OperationalError

import walkoff.cache
import walkoff.config
import walkoff.executiondb
import walkoff.scheduler

logger = logging.getLogger(__name__)


class Context(object):

    def __init__(self, init_all=True, executor=True):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        try:
            self.execution_db = walkoff.executiondb.ExecutionDatabase(walkoff.config.Config.EXECUTION_DB_TYPE,
                                                                      walkoff.config.Config.EXECUTION_DB_PATH,
                                                                      walkoff.config.Config.EXECUTION_DB_HOST)
        except OperationalError as e:
            if "password" in str(e):
                logger.error("Incorrect username and/or password for execution database. Please make sure these are "
                             "both set correctly in their respective environment variables and try again."
                             "Error Message: {}".format(str(e)))
            else:
                logger.error("Error connecting to execution database. Please make sure all database settings are "
                             "correct and try again. Error Message: {}".format(str(e)))
            os._exit(1)

        if init_all:
            self.cache = walkoff.cache.make_cache(walkoff.config.Config.CACHE)
            if executor:
                import walkoff.multiprocessedexecutor.multiprocessedexecutor as executor
                self.executor = executor.MultiprocessedExecutor(self.cache, walkoff.config.Config)
                self.scheduler = walkoff.scheduler.Scheduler()

    def inject_app(self, app):
        self.scheduler.app = app
