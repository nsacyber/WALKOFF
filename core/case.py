import uuid, datetime, sys

class Case(object):
    def __init__(self, id="", history=[], subscriptions=[]):
        self.id = id
        self.uid = uuid.uuid4()
        self.history = history
        self.enabled = False
        self.subscriptions = subscriptions

    def __enter__(self):
        self.enabled = True

    def __exit__(self,exception_type, exception_value, traceback):
        self.enabled = False

    def connectToEvents(self, controllers):
        for c in controllers:
            for subscription in self.subscriptions:
                if c.name == subscription:
                    for event in self.subscriptions[subscription]:
                        sender = getattr(c, event)
                        handler = getattr(sys.modules[__name__], event)
                        sender.connect(handler)

    def addEvent(self, event):
        self.history.append(event)


cases = {}
def addCase(name, case, controllers):
    if name not in cases:
        cases[name] = case
        #cases[name].connectToEvents(controllers)
        return True
    return False

def addEntryToCase(controller, type, message, data=None):
    event = {
        "uuid" : str(uuid.uuid4()),
        "timestamp" : str(datetime.datetime.utcnow()),
        "type" : type,
        "controller" : controller.name,
        "message" : message,
        "data" : data
    }

    for case in cases:
        if cases[case].enabled:
            if controller.name in cases[case].subscriptions:
                cases[case].addEvent(event=event)
    return event

def schedulerStart(sender):
    addEntryToCase(controller=sender, type="SYSTEM", message="Scheduler started")

def schedulerShutdown(sender, case="default"):
    addEntryToCase(controller=sender, type="SYSTEM", message="Scheduler shutdown")

def schedulerPaused(sender, case="default"):
    addEntryToCase(controller=sender, type="SYSTEM", message="Scheduler paused")

def schedulerResumed(sender, case="default"):
    addEntryToCase(controller=sender, type="SYSTEM", message="Scheduler resumed")

def jobAdded(sender, case="default"):
    addEntryToCase(controller=sender, type="SYSTEM", message="Job added")

def jobRemoved(sender, case="default"):
    addEntryToCase(controller=sender, type="SYSTEM", message="Job removed")

def jobExecuted(sender, case="default"):
    addEntryToCase(controller=sender, type="SYSTEM", message="Job executed")

def jobException(sender, case="default"):
    addEntryToCase(controller=sender, type="SYSTEM", message="Job executed with exception")


