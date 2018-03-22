from logging import Handler
from walkoff.events import WalkoffEvent

class ConsoleLoggingHandler(Handler):
    def emit(self, record):
        log_entry = self.format(record)
        WalkoffEvent.ConsoleLogged.signal.send(self, data=log_entry)