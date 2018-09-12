import walkoff.cache
import walkoff.executiondb
import walkoff.scheduler


class Context(object):

    def __init__(self, config, init_all=True):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.

        Args:
            config (Config): A config object
        """
        self.execution_db = walkoff.executiondb.ExecutionDatabase(config.EXECUTION_DB_TYPE, config.EXECUTION_DB_PATH)

        if init_all:
            import walkoff.multiprocessedexecutor.multiprocessedexecutor as executor
            self.cache = walkoff.cache.make_cache(config.CACHE)
            self.executor = executor.MultiprocessedExecutor(self.cache, config)
            self.scheduler = walkoff.scheduler.Scheduler()

    def inject_app(self, app):
        self.scheduler.app = app
