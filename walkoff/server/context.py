class Context(object):
    def __init__(self):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        import walkoff.core.controller

        self.controller = walkoff.core.controller.controller


running_context = Context()
