import walkoff.cache
import walkoff.executiondb
import walkoff.multiprocessedexecutor.multiprocessedexecutor as executor
import walkoff.scheduler
from walkoff.worker.action_exec_strategy import make_execution_strategy


class Context(object):

    def __init__(self, config):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.

        Args:
            config (Config): A config object
        """
        self.execution_db = walkoff.executiondb.ExecutionDatabase(config.EXECUTION_DB_TYPE, config.EXECUTION_DB_PATH)

        self.cache = walkoff.cache.make_cache(config.CACHE)
        action_execution_strategy = make_execution_strategy(config)
        self.executor = executor.MultiprocessedExecutor(self.cache, action_execution_strategy)
        self.scheduler = walkoff.scheduler.Scheduler()

    def inject_app(self, app):
        self.scheduler.app = app