from apps import App, action
from xml.dom import minidom
import requests, json


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.device = self.get_device()
        self.base_url = "https://" + self.device.ip + ":" + str(self.device.port)
        self.s = requests.Session()
        self.session_key = None
        self.connect()

    def connect(self):
        url = self.base_url + "/services/auth/login"
        payload = {'username': self.get_device().username, 'password': self.get_device().get_password()}
        headers = {'content-type': 'application/json'}
        r = self.s.post(url, data=payload, verify=False, headers=headers)

        if 200 <= r.status_code <= 400:
            self.session_key = minidom.parseString(r.text).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue

        return json.dumps({"status": "connected"})

    @action
    def search(self, query, max_count, spawn_process, output_mode, exec_type):

        if self.session_key:
            if not query.startswith('search'):
                query = ("search " + query)

            body = {"search": query}
            if max_count:
                body["max_count"] = max_count

            if spawn_process is not None:
                body["spawn_process"] = spawn_process

            if output_mode:
                body["output_mode"] = output_mode

            url = self.base_url + "/services/search/jobs"
            if exec_type:
                url = '{0}/{1}'.format(url, exec_type)

            headers = {"Authorization": "Splunk " + self.session_key, 'content-type': 'application/json'}

            r = self.s.post(url, headers=headers, data=body, verify=False)

            results = r.json()["results"]

            return results

    def shutdown(self):
        print("Splunk Shutting Down")
        return
