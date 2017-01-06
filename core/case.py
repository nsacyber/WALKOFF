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

    def addEvent(self, event):
        self.history.append(event)


cases = {}
def addCase(name, case):
    if name not in cases:
        cases[name] = case
        return True
    return False

def addEntryToCase(caller, type, message, data=None):
    event = {
        "uuid" : str(uuid.uuid4()),
        "timestamp" : str(datetime.datetime.utcnow()),
        "type" : type,
        "controller" : caller.name,
        "message" : message,
        "data" : data
    }

    for case in cases:
        if cases[case].enabled:
            if type == "SYSTEM":
                if caller.name in cases[case].subscriptions:
                    cases[case].addEvent(event=event)
            elif type == "WORKFLOW":
                if caller.parentController in cases[case].subscriptions:
                    cases[case].addEvent(event=event)
    return event

"""
    Scheduler Event Handlers
"""
def schedulerStart(sender):
    addEntryToCase(caller=sender, type="SYSTEM", message="Scheduler started")

def schedulerShutdown(sender, case="default"):
    addEntryToCase(caller=sender, type="SYSTEM", message="Scheduler shutdown")

def schedulerPaused(sender, case="default"):
    addEntryToCase(caller=sender, type="SYSTEM", message="Scheduler paused")

def schedulerResumed(sender, case="default"):
    addEntryToCase(caller=sender, type="SYSTEM", message="Scheduler resumed")

def jobAdded(sender, case="default"):
    addEntryToCase(caller=sender, type="SYSTEM", message="Job added")

def jobRemoved(sender, case="default"):
    addEntryToCase(caller=sender, type="SYSTEM", message="Job removed")

def jobExecuted(sender, case="default"):
    addEntryToCase(caller=sender, type="SYSTEM", message="Job executed")

def jobException(sender, case="default"):
    addEntryToCase(caller=sender, type="SYSTEM", message="Job executed with exception")

"""
    Workflow Execution Event Handlers
"""

def instanceCreated(sender):
    addEntryToCase(caller=sender, type="WORKFLOW", message="New instance created")

def stepExecutedSuccessfully(sender):
    addEntryToCase(caller=sender, type="WORKFLOW", message="Step Executed")

def nextStepFound(sender):
    addEntryToCase(caller=sender, type="WORKFLOW", message="Next step found")

def workflowShutdown(sender):
    addEntryToCase(caller=sender, type="WORKFLOW", message="Workflow shut down")
