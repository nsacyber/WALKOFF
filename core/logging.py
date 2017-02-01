from core import config
import blinker

# Signals
executed = blinker.signal("executed")
next = blinker.signal("next")


# Event Handlers
class ExecutedReciever:
    def __init__(self):
        def handleExecuted(sender, **kwargs):
            self.onExecuted(sender, **kwargs)

        self.handleExecuted = handleExecuted
        executed.connect(handleExecuted)

    def onExecuted(self, sender, **kwargs):
        print("STEP EXECUTED")


class NextReciever:
    def __init__(self):
        def handleNext(sender, **kwargs):
            self.onNext(sender, **kwargs)

        self.handleNext = handleNext
        next.connect(handleNext)

    def onNext(self, sender, **kwargs):
        print(sender, "NEXT STEP CHOSEN")


# Recievers
er = ExecutedReciever()
n = NextReciever()


# Logging Decorators
def logEvent(action):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retVal = func(*args, **kwargs)
            if config.logSettings[action]:
                globals()[action].send()
            return retVal

        return wrapper

    return decorator
