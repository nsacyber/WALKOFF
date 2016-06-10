from blinker import Namespace
from core import execution

#Set up signals
signals = Namespace()

status = signals.signal("update")
status.connect(execution.update)

#Execution Actions, Signal Recievers
def start(sender):
    status.send(sender, status="start")
    return "started"

def stop(sender):
    status.send(sender, status="stop")
    return "stopped"

def pause(sender):
    return "paused"

def shutdown(sender):
    return "shutdown"
