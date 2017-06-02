from apps import App
from xml.dom import minidom
import requests, json


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.baseURL = "https://" + self.config.ip + ":" + str(self.config.port)
        self.s = requests.Session()
        self.sessionKey = None
        self.connect()

    def connect(self, args={}):
        url = self.baseURL + "/services/auth/login"
        payload = {'username': self.config.username, 'password': self.config.password}
        headers = {'content-type': 'application/json'}
        r = self.s.post(url, data=payload, verify=False, headers=headers)

        if 200 <= r.status_code <= 400:
            self.sessionKey = minidom.parseString(r.text).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue

        return json.dumps({"status": "connected"})

    def search(self, args={}):

        if "query" in args and self.sessionKey:
            query = args["query"]()
            if not query.startswith('search'):
                query = ("search " + query)

            body = {"search": query}
            if "max_count" in args:
                body["max_count"] = args["max_count"]()

            if "spawn_process" in args:
                body["spawn_process"] = args["spawn_process"]()

            if "output_mode" in args:
                body["output_mode"] = args["output_mode"]()

            url = self.baseURL + "/services/search/jobs"
            if "exec_type" in args:
                url = url + "/" + args["exec_type"]()

            headers = {"Authorization": "Splunk " + self.sessionKey, 'content-type': 'application/json'}

            r = self.s.post(url, headers=headers, data=body, verify=False)

            results = r.json()["results"]

            return results

    def shutdown(self):
        print "Splunk Shutting Down"
        return
