class Context(object):
    def __init__(self):
        """Initializes a new Context object. This acts as an interface for objects to access other event specific
            variables that might be needed.
        """
        from server.app import app
        import core.controller
        from server.messaging import Message

        self.flask_app = app
        self.controller = core.controller.controller
        self.Message = Message


running_context = Context()
