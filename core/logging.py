from blinker import Namespace
import uuid, time, json, os

#Loggging Variables
#Types
ERROR = "Error"
MESSAGE = "Message"

#Sources
INTERFACE = "Interface"
SYSTEM = "System"
EXECUTION = "Execution"


class Logger():
    def __init__(self):
        self.signals = Namespace()
        self.log = self.signals.signal("log")
        self.log.connect(self.logMessage)

    def writeLog(self, message):
        try:
            name = "shortstopEngine_" + time.strftime("%d%b%Y") + ".log"
            path = "data/logs/"
            with open(os.path.abspath(path + name), "a") as f:
                f.write(message)
            return True
        except Exception as e:
            return False


    def logMessage(self, sender=None, message="", type="", source=""):
        try:
            id = uuid.uuid4().int
            log = {"uuid": id, "type": type, "source": source, "message" : message}
            if self.writeLog(json.dumps(log) + ","):
                return True
            return False
        except Exception as e:
            print e
            return False

logger = Logger()

