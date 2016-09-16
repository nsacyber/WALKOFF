import re, json, importlib

class Step:
    def __init__(self, id=None, to=[], app="", device=[], action="", input={}, error=[], **kwargs):
        self.id = id
        self.to = to
        self.app = app
        self.device = device
        self.action = action
        self.input = input
        self.error = error

        self.out = {}
        for key, value in kwargs.items():
            setattr(self, key, value)

    def setOut(self, device, value):
        self.out[device] = value

    def setupArguments(self):
        re_tag = "<-(.*?)->"
        args = {}
        for x in self.input.keys():
            tags = re.findall(re_tag, str(self.input[x]))

            args[x] = []
            for tag in tags:
                args[x].append(json.loads(tag))

        return args

    def setupDevices(self):
        re_tag = "<-(.*?)->"
        devices = []
        args = {}
        for d in self.device:
            tags = re.findall(re_tag, str(d))
            if len(tags) > 0:
                device = tags[0]

                try:
                    args = json.loads(device)
                except Exception as e:
                    print "ERROR"
                    print e

                #"All" returns all the devices for a specific app
                if args["device"] == "all":
                    from api.mainAPI import Device
                    query = Device.query.filter_by(app=self.app).with_entities(Device.name).all()
                    devices = list({k[0] for k in query})
                    self.device = devices

    def setInputValue(self, key, value):
        self.input[key] = value

    def editStep(self, id=None, to=None, app=None, device=None, action=None, input=None, error=None):
        if id != None and id != "":
            self.id = id
        if to != None and to != "":
            self.to = to
        if app != None and app != "":
            self.app = app
        if device != None and device != "":
            self.device = device
        if action != None and action != "":
            self.action = action
        if input != None and input != "":
            self.input = input
        if error != None and error != "":
            self.error = error

    def getStepData(self):
        result = dict()
        result["id"] = self.id
        result["to"] = self.to
        result["device"] = self.device
        result["app"] = self.app
        result["action"] = self.action
        result["in"] = self.input
        result["error"] = self.error
        return result

    def execute(self, instance=None):
        result = getattr(instance, self.action)(args=self.input)
        if result != None:
            return result
        else:
            return ""

    def executeFlag(self, args, value, function):
        #Checks if the flag exists
        try:
            flagModule = importlib.import_module("core.flags." + function)
        except ImportError as e:
            flagModule = None

        if flagModule and args and value:
            result = getattr(flagModule, "main")(args=args, value=value)
            return result
        return None


    def executeFilter(self, function, args, value):
        try:
            filterModule = importlib.import_module("core.filters." + function)
        except ImportError as e:
            filterModule = None

        if filterModule:
            result = getattr(filterModule, "main")(args=args, value=value)
            return result
        return None

    def nextStep(self, path):
        if len(path) > 0 and self.out != None:
            #For each potential Path
            for option in path:
                flags = 0
                if "conditions" in option:
                    #For each check
                    for valueTest in option["conditions"]:

                        #Execute Filters Before Conditionals
                        out = self.out
                        filters = valueTest["filters"]
                        for filter in filters:
                            out = self.executeFilter(function=filter["filter"], args=filter["args"], value=out)

                        flagModule = None
                        function = valueTest["flag"]
                        args = valueTest["args"]

                        result = self.executeFlag(args=args, value=out, function=function)

                        if result:
                            flags+=1

                        if flags == len(option["conditions"]):
                            return option["next"]

        return "<-[status:play_end]->"

    def __repr__(self):
        #return '{{"id":"{self.id}", "to":{self.to}, "device":"{self.device}", "app":"{self.action}", "action":"{self.app}", "in":{self.input}, "error":{self.error} }}'.format(self=self)
        result = dict()
        result["id"] = self.id
        result["to"] = self.to
        result["device"] = str(self.device)
        result["app"] = self.app
        result["action"] = self.action
        result["in"] = self.input
        result["error"] = self.error
        result["out"] = self.out
        return json.dumps(result)
