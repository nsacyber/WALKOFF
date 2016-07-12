from core import app
import requests, json, xml.etree.ElementTree as ET

class Main(app.App):
    def __init__(self,name=None, device=None):
        app.App.__init__(self, name, device)
        self.s = requests.Session()
        self.ip = self.config.ip + ":" + str(self.config.port)
        url = 'https://' + self.ip + '/api/?type=keygen&user=' + self.config.username + '&password=' + self.config.password
        r = self.s.get(url, verify=False)

        tree = ET.fromstring(r.text)
        if tree.attrib['status'] == 'success':
            print "success!"
            #self.keySuffix = '&key=' + tree[0][0].text
            self.keySuffix = tree[0][0].text

    #Actions
    def commit(self, args={}):
        url = 'http(s)://' + self.ip + '/api/?type=commit&cmd=<commit></commit>'
        r = self.get(url, verify=False)
        return r.text

    def validate(self, args={}):
        url = 'https://' + self.ip + '/api/?type=commit&cmd=<commit><validate></validate></commit>'
        r = self.get(url, verify=False)
        return r.text

    def setCustomURL(self, args={}):
        element = '<member>' + args['e'] + '</member>'

        xpath = "/config/devices/entry/vsys/entry/profiles/custom-url-category/entry[@name='" + args['name'] + "]'/list"

        url = 'https://' + self.ip + '/api/'
        payload = {'type' : 'config', 'action' : 'set', 'xpath' : xpath, 'element' : element, 'key' : self.keySuffix}

        r = self.s.get(url, params=payload, verify=False)

        return r.text

    def setCustomFilterIP(self, args={}):
        element = '<entry name="' + args['name'] + '"><url>' + args['ip'] + '</url><description>' + args['description'] + '</description></entry>'

        xpath = "/config/devices/entry/vsys/entry/external-list/entry[@name='" + args['name'] + "']"

        url = 'https://' + self.ip + '/api/'
        payload = {'type' : 'config', 'action' : 'set', 'xpath' : xpath, 'element' : element, 'key' : self.keySuffix}

        r = self.s.get(url, params=payload, verify=False)

        print r.text
        return r.text

    def addElementToDynamicBlockList(self, args={}):
        element = '<entry name="' + args['name'] + '"><url>' + args['ip'] + '</url><description>' + args['description'] + '</description></entry>'

        xpath = "/config/devices/entry/vsys/entry/external-list"

        url = 'https://' + self.ip + '/api/'
        payload = {'type' : 'config', 'action' : 'set', 'xpath' : xpath, 'element' : element, 'key' : self.keySuffix}

        r = self.s.get(url, params=payload, verify=False)

        print r.text
        return r.text

    #Information
    def getRunningConfiguration(self, args={}):
        url = 'https://' + self.ip + '/api/?type=config&action=show'
        payload = {'key' : self.keySuffix}
        r = self.s.get(url, params=payload, verify=False)
        print r.text
        return {"config" : r.text}

    def getURLFilteringConfig(self, args={}):
        url = 'https://' + self.ip + '/api/?type=config&action=show&xpath=/config/shared/profiles/url-filtering' + self.keySuffix
        r = self.s.get(url, verify=False)
        return r.text

    def getCustomURLCategory(self, args={}):
        url = 'https://' + self.ip + '/api/?type=config&action=show&xpath=/config/devices/entry/vsys/entry/profiles/custom-url-category&key=' + self.keySuffix
        r = self.s.get(url, verify=False)
        return r.text

    def shutdown(self):
        print "Palo Alto Shutting Down"
        return