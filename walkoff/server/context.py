import walkoff.cache
import walkoff.case.database
import walkoff.executiondb
import walkoff.multiprocessedexecutor.multiprocessedexecutor as executor
import walkoff.scheduler
from walkoff.case.logger import CaseLogger
from walkoff.case.subscription import SubscriptionCache
from walkoff.worker.actionexecstrategy import make_execution_strategy


class Context(object):

    def __init__(self, config):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.

        Args:
            config (Config): A config object
        """
        self.execution_db = walkoff.executiondb.ExecutionDatabase(config.EXECUTION_DB_TYPE, config.EXECUTION_DB_PATH)
        self.case_db = walkoff.case.database.CaseDatabase(config.CASE_DB_TYPE, config.CASE_DB_PATH)

        self.subscription_cache = SubscriptionCache()
        self.case_logger = CaseLogger(self.case_db, self.subscription_cache)
        self.cache = walkoff.cache.make_cache(config.CACHE)
        action_execution_strategy = make_execution_strategy(config)
        self.executor = executor.MultiprocessedExecutor(self.cache, self.case_logger, action_execution_strategy)
        self.scheduler = walkoff.scheduler.Scheduler(self.case_logger)

    def inject_app(self, app):
        self.scheduler.app = app