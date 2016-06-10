from blinker import Namespace
from signals import executionSignals as execution

class Execution():
    def __init__(self):
        self.signals = Namespace()

        self.start = self.signals.signal("start")
        self.start.connect(execution.start)

        self.stop = self.signals.signal("stop")
        self.stop.connect(execution.stop)

        self.pause = self.signals.signal("pause")
        self.pause.connect(execution.pause)

        self.shutdown = self.signals.signal("shutdown")
        self.shutdown.connect(execution.shutdown)

    #Actions
    def post(self, action, **kwargs):
        if action == "start":
            self.start.send(self)
        elif action == "stop":
            self.stop.send(self)
        return {}