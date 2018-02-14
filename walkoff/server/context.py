class Context(object):
    def __init__(self):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        import walkoff.multiprocessedexecutor.multiprocessedexecutor
        import walkoff.core.scheduler

        self.executor = walkoff.multiprocessedexecutor.multiprocessedexecutor.multiprocessedexecutor
        self.scheduler = walkoff.core.scheduler.scheduler


running_context = Context()
