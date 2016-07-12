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

    #Executes the play
    def executePlay(self, q=Queue(), start="start", instances={"system":None}):
        #Updates lastRun
        status = {"name" : self.name, "lastRun": datetime.datetime.now()}

        #initializes instances
        i = instances

        #Stores the results of each step to return
        outputs = []

        current = start
        while current != "<-[status:play_end]->" and current != None:

            #Create instance for uninstanciated commands
            if self.steps[current].device not in instances:
                instance = self.createInstance(self.steps[current].app, self.steps[current].device)
                if instance != None:
                    i[self.steps[current].device] = instance

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



            #Executes step and sets the return value
            try:
                out = self.steps[current].execute(i[self.steps[current].device])
                if not isinstance(out, str):
                    out = json.dumps(out, ensure_ascii=True, default=str)
                self.steps[current].setOut(out)

                #Adds log of execution
                outputs.append(str(self.steps[current]))

                #Decides where to go next
                current = self.steps[current].nextStep(self.steps[current].to)

            except Exception as e:
                print "ERROR"
                print e
                self.steps[current].setOut(str(e))

                #Adds log of execution
                outputs.append(json.dumps(self.steps[current]), ensure_ascii=True, default=str, indent=2)

                current = self.steps[current].nextStep(self.steps[current].error)



        status["status"] = "<-[status:play_executed]->"
        #Cycles through instances and executes shutdown procedures
        for instance in instances:
            if instances[instance].__class__.__base__.__name__ == app.App.__name__:
                instances[instance].shutdown()

        q.put(status)
        return outputs