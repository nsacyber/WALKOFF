class Context(object):
    def __init__(self):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        import walkoff.controller

        self.controller = walkoff.controller.controller


running_context = Context()
