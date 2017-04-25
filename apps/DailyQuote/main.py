from server import appdevice
import requests
import json


# There is an associated Daily Quote test workflow which can be executed

class Main(appdevice.App):
    def __init__(self, name=None, device=None):
        # The parent app constructor looks for a device configuration and returns that as a
        # dictionary called self.config
        appdevice.App.__init__(self, name, device)
        self.introMessage = {"message": "Quote App"}
        self.baseUrl = "http://quotes.rest/qod.json?category=inspire"
        self.s = requests.Session()

    # Returns the message defined in init above
    def quoteIntro(self, args={}):
        # LOOK AT YOUR CONSOLE WHEN EXECUTING
        return self.introMessage

    # Returns the argument that was passed to it. Used to test passing arguments
    def repeatBackToMe(self, args={}):
        # print("REPEATING: " + args["call"]())
        return "REPEATING: " + args["call"]()

    # Uses argument passed to function to make an api request
    def forismaticQuote(self, args={}):
        headers = {'content-type': 'application/json'}
        url = args["url"]()
        payload = {'method': 'getQuote', 'format': 'json', 'lang': 'en'}
        result = self.s.get(url, params=payload, verify=False)
        try:
            json_result = json.loads(result.text)
            json_result['success'] = True
            return json_result
        except:
            return {'success': False, 'text': result.text}

    # Uses the url defined in _init to make a getQuote api call and returns the quote
    def getQuote(self, args={}):
        headers = {'content-type': 'application/json'}
        url = self.baseUrl
        result = self.s.get(url, headers=headers, verify=False)
        return result.json()

    def shutdown(self):
        return
