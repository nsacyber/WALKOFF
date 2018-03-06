import json

import requests

from apps import App, action


# There is an associated Daily Quote test workflow which can be executed

class DailyQuote(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.introMessage = {"message": "Quote App"}
        self.baseUrl = "http://quotes.rest/qod.json?category=inspire"
        self.s = requests.Session()

    # Returns the message defined in init above
    @action
    def quoteIntro(self):
        return self.introMessage

    @action
    def repeatBackToMe(self, call):
        return "REPEATING: " + call

    # Uses argument passed to function to make an api request
    @action
    def forismaticQuote(self, url):
        headers = {'content-type': 'application/json'}
        payload = {'method': 'getQuote', 'format': 'json', 'lang': 'en'}
        result = self.s.get(url, params=payload, verify=False)
        try:
            json_result = json.loads(result.text)
            json_result['success'] = True
            return json_result
        except:
            return {'success': False, 'text': result.text}

    # Uses the url defined in _init to make a getQuote api call and returns the quote
    @action
    def getQuote(self):
        headers = {'content-type': 'application/json'}
        url = self.baseUrl
        result = self.s.get(url, headers=headers, verify=False)
        return result.json()

    def shutdown(self):
        return
