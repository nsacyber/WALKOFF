import step, datetime, sys, importlib, logging, uuid, json
from multiprocessing import Queue
import flagsFiltersKeywords as ffk
import app

class Play():
    def __init__(self, name, data):
        self.options = data["options"]
        self.steps = self.loadSteps(data["play"])
        self.lastRun = datetime.datetime.strptime("1900-1-1 1:1:1", "%Y-%m-%d %H:%M:%S")
        self.name = name
        self.uuid = uuid.uuid4()
        self.start = "start"
        self.instances = {"system":None}

    def loadSteps(self, data):
        steps = {}
        for stepData in data:
            steps[stepData["id"]] = step.Step(stepData["id"], stepData["to"], stepData["app"], stepData["device"], stepData["action"], stepData["in"], stepData["error"], optional="optional")
        return steps

    def getOption(self, key):
        return self.options[key]

    def getLastRun(self):
        return self.lastRun

    def setLastRun(self, time):
        self.lastRun = time

    def getStep(self, key):
        if key in self.steps:
            return self.steps[key]

    def addStep(self, id=None, to=[], app="", device="", action="", input={}, error=[]):
        if id == None:
            id = str(len(self.steps))
            if len(self.steps) == 0:
                id = "start"


        self.steps[id] = step.Step(id, to, app, device, action, input, error)
        return {"status" : "added new step"}

    def removeStep(self, key):
        if key in self.steps:
            del self.steps[key]
            return {"status" : "step removed"}
        else:
            return {"status" : "step could not be removed"}

    #Checks if the app has already been imported
    def checkImports(self, app):
        #checks for the proper imports
        module = 'apps.' + app + '.main'
        try:
            return sys.modules[module]
        except KeyError:
            pass
        try:
            return importlib.import_module(module, 'Main')
        except ImportError as e:
            logging.logger.logMessage(message=e.message, source="App: " + app, type="ERROR")

    #Creates instance of the app
    def createInstance(self, app, device=None):
        imported = self.checkImports(app)
        if imported != None:
            return getattr(imported, 'Main')(name=app, device=device)
        else:
            return None

    def setupStep(self, current):
        self.steps[current].setupDevices()

        #Parses arguments for input tags
        args = self.steps[current].setupArguments()
        if len(args.keys()) > 0:
            for key in args.keys():
                for tags in args[key]:
                    try:
                        keywordModule = importlib.import_module("core.keywords." + tags["action"])
                    except ImportError as e:
                        keywordModule = None

                    if keywordModule:
                        result = getattr(keywordModule, "main")(steps=self.steps, args=tags["args"])

                        for filter in tags["filters"]:
                            result = ffk.executeFilter(function=filter["filter"], args=filter["args"], value=result)

                        self.steps[current].setInputValue(key, result)

    def executeStep(self, i, d, current):
        #Executes step and sets the return value
        try:
            out = self.steps[current].execute(i[d])
            #if not isinstance(out, str):
                #out = str(out, ensure_ascii=True, default=str)
            self.steps[current].setOut(str(d), out)

            #Adds log of execution
            outputs = self.steps[current]

            #Decides where to go next
            nextStep = self.steps[current].nextStep(self.steps[current].to)
            return outputs, nextStep

        except Exception as e:
            self.steps[current].setOut(i[d], str(e))

            #Adds log of execution
            outputs = str(self.steps[current])

            # Decides where to go next
            nextStep = self.steps[current].nextStep(self.steps[current].error)
            return outputs, nextStep



    def executePlay(self, q=Queue(), start="start", instances={}, output={}):
        self.setupStep(start)
        #If there is more than one device assigned to an action execute those actions before moving on
        for d in self.steps[start].device:
            if d not in instances:
                instance = self.createInstance(self.steps[start].app, d)
                if instance != None:
                    instances[d] = instance
                else:
                    instances[d] = None

            o, next = self.executeStep(i=instances, d=d, current=start)
            key = str(uuid.uuid4())
            output = o

            #Continues that device's workflow independently
            if next != "<-[status:play_end]->" and next != None:
                output, instances = self.executePlay(q=q, start=next, instances=instances, output=output)

            elif next == "<-[status:play_end]->":
                instance = d
                if instances[instance].__class__.__base__.__name__ == app.App.__name__:
                    instances.pop(instance, None).shutdown()

        return output, instances
