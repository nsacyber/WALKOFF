class Context(object):
    def __init__(self):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        import walkoff.multiprocessedexecutor.multiprocessedexecutor as executor
        import walkoff.scheduler
        from walkoff.case.logger import CaseLogger
        import walkoff.case.database as casedb
        import walkoff.cache

        self.case_logger = CaseLogger(casedb.case_db)
        self.cache = walkoff.cache.make_cache()
        self.executor = executor.MultiprocessedExecutor(self.cache, self.case_logger)
        self.scheduler = walkoff.scheduler.Scheduler(self.case_logger)


running_context = Context()
