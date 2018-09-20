import walkoff.cache
import walkoff.executiondb
import walkoff.scheduler
from walkoff.worker.action_exec_strategy import make_execution_strategy
import walkoff.config


class Context(object):

    def __init__(self, init_all=True, executor=True):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        self.execution_db = walkoff.executiondb.ExecutionDatabase(walkoff.config.Config.EXECUTION_DB_TYPE,
                                                                  walkoff.config.Config.EXECUTION_DB_PATH)

        if init_all:
            self.cache = walkoff.cache.make_cache(walkoff.config.Config.CACHE)
            if executor:
                import walkoff.multiprocessedexecutor.multiprocessedexecutor as executor
                action_execution_strategy = make_execution_strategy(walkoff.config.Config)
                self.executor = executor.MultiprocessedExecutor(self.cache, action_execution_strategy)
                self.scheduler = walkoff.scheduler.Scheduler()

    def inject_app(self, app):
        self.scheduler.app = app
