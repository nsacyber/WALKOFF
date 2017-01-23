import uuid, datetime

class Case(object):
    def __init__(self, id="", history=[], subscriptions={}):
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
    if hasattr(caller, "name"):
        name = caller.name
    else:
        name  = caller.id

    event = {
        "uuid" : str(uuid.uuid4()),
        "timestamp" : str(datetime.datetime.utcnow()),
        "type" : type,
        "caller" : name,
        "message" : message,
        "data" : data
    }

    for case in cases:
        if cases[case].enabled:
            for key in cases[case].subscriptions:
                if type == "SYSTEM":
                    if caller.name in cases[case].subscriptions:
                        cases[case].addEvent(event=event)
                elif type == "WORKFLOW":
                    if caller.parentController in cases[case].subscriptions:
                        cases[case].addEvent(event=event)
                elif type == "STEP":
                    subs = key.split(":")
                    if caller.parent in subs:
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
    addEntryToCase(caller=sender, type="WORKFLOW", message="Step executed")

def nextStepFound(sender):
    addEntryToCase(caller=sender, type="WORKFLOW", message="Next step found")

def workflowShutdown(sender):
    addEntryToCase(caller=sender, type="WORKFLOW", message="Workflow shut down")



"""
    Step Execution Event Handlers
"""

def functionExecutedSuccessfully(sender):
    addEntryToCase(caller=sender, type="STEP", message="Function executed successfully")

def inputValidated(sender):
    addEntryToCase(caller=sender, type="STEP", message="Input successfully validated")

def conditionalsExecuted(sender):
    addEntryToCase(caller=sender, type="STEP", message="Conditionals executed")


"""
    Next Execution Event Handlers
"""

def stepTaken(sender):
    addEntryToCase(caller=sender, type="NEXT", message="Step taken")

def stepNotTaken(sender):
    addEntryToCase(caller=sender, type="NEXT", message="Step not taken")



