from server import appDevice
import requests, json

# There is an associated Daily Quote test workflow which can be executed

class Main(appDevice.App):
    def __init__(self, name=None, device=None):
        #The parent app constructor looks for a device configuration and returns that as a dictionary called self.config
        appDevice.App.__init__(self, name, device)
        self.introMessage = {"message":"Quote App"}
        self.baseUrl = "http://quotes.rest/qod.json?category=inspire"
        self.s = requests.Session()

    # Returns the message defined in init above
    def quoteIntro(self, args={}):
        # LOOK AT YOUR CONSOLE WHEN EXECUTING
        print("testing quote intro")
        return self.introMessage

    # Returns the argument that was passed to it. Used to test passing arguments
    def repeatBackToMe(self, args={}):
        # print("REPEATING: " + args["call"]())
        return "REPEATING: " + args["call"]()

    #Uses argument passed to function to make an api request
    def forismaticQuote(self, args={}):
        headers = {'content-type': 'application/json'}
        url = args["url"]()
        payload = {'method':'getQuote','format':'json','lang':'en'}
        result = self.s.get(url, params=payload,verify=False)
        jsonResult = result.json()
        jsonResult['success'] = True
        return jsonResult

    # Uses the url defined in _init to make a getQuote api call and returns the quote
    def getQuote(self, args={}):
        headers = {'content-type': 'application/json'}
        url = self.baseUrl
        result =self.s.get(url,headers=headers, verify=False)
        return  result.json()


    def shutdown(self):
        return
