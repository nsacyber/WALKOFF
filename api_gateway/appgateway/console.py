from logging import Handler

from api_gateway.events import WalkoffEvent


class ConsoleLoggingHandler(Handler):
    def emit(self, record):
        log_entry = self.format(record)
        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConsoleLog, message=log_entry, level=self.level)
