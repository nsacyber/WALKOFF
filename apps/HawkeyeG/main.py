from core import app

import requests, json, sys
from bs4 import BeautifulSoup

class Main(app.App):
    def __init__(self, name=None, device=None):
        app.App.__init__(self, name, device)
        self.s = requests.Session()
        self.ip = self.config.ip + ":" + str(self.config.port)

    def connect(self, args=None):
        try:
             #Login Info
            loginPage = 'https://' + self.ip + '/interface/login'
            loginRequest = 'https://' + self.ip + '/interface/j_spring_security_check'

            login = self.s.get(loginPage, verify=False)
            soup = BeautifulSoup(login.content, "html.parser")

            self.csrf = soup.find('input', attrs={'name':'_csrf', 'type':'hidden'})

            loginParam = {"j_password":self.config.password, "j_username":self.config.username, "login":"", "_csrf":self.csrf['value']}
            self.loginParam = loginParam

            r = self.s.request('POST', loginRequest, params=loginParam, verify=False)

            return "CONNECTED!"
        except Exception as e:
            print "HAWKEYE" + str(e)
            return {"status": "Could not connect"}

    def close(self, args=None):
        try:
            print "closing connection"
            self.s.close()
            return {}
        except:
            print "Could not close connection"
            return {"status": "Could not close connection"}

    #Functionality
    #Upload MD5 Threat Signature
    def uploadMD5(self, args=None):
        try:

            r = self.s.get("https://" + self.ip + "/interface/app/#/md5-threat-management", verify=False)
            soup = BeautifulSoup(r.content, "html.parser")
            self.csrf = soup.find('input', attrs={'name':'_csrf', 'type':'hidden'})


            url = 'https://' + self.ip + '/interface/rest/md5-threats/json'

            payload = {'comments':args["comments"], 'md5':args["md5"], 'name':args["name"]}
            head = {"X-CSRF-TOKEN" : str(self.csrf["value"]), "X-Requested-By" : "HawkeyeG_XMLHttpRequest"}

            r = self.s.request('POST', url,  headers=head, data=payload, verify=False)

            return r.text
        except Exception as e:
            print "Could not upload Md5"
            print e
            return {"status": "error"}

    #Scan specific host
    def scanHost(self,  args=None):

        r = self.s.get("https://" + self.ip + "/interface/app/#/md5-threat-management", verify=False)
        soup = BeautifulSoup(r.content, "html.parser")
        self.csrf = soup.find('input', attrs={'name':'_csrf', 'type':'hidden'})

        try:
            url = 'https://' + self.ip + '/interface/rest/devices/' + str(args['d']) + '/runSurvey'
            payload = {'id':args['d'], 'password': "", 'templateId':args['t']}

            head = {"X-CSRF-TOKEN" : str(self.csrf["value"]), "X-Requested-By" : "HawkeyeG_XMLHttpRequest"}

            r = self.s.request('POST', url, headers=head, data=payload, verify=False)
            print r.status_code
            return "OK"
        except Exception as e:
            try:
                r = self.s.get("https://" + self.ip + "/interface/app/#/md5-threat-management", verify=False)
                soup = BeautifulSoup(r.content, "html.parser")
                self.csrf = soup.find('input', attrs={'name':'_csrf', 'type':'hidden'})

                url = 'https://' + self.ip + '/interface/rest/devices/' + str(args['d']) + '/runSurvey'
                payload = {'id':args['d'], 'password': "", 'templateId':args['t']}

                head = {"X-CSRF-TOKEN" : str(self.csrf["value"]), "X-Requested-By" : "HawkeyeG_XMLHttpRequest"}

                r = self.s.request('POST', url, headers=head, data=payload, verify=False)
                print r.status_code
                return "OK"
            except Exception as e:
                print "failed twice"
                print e.message
                return {"status" : "Error"}

    def scanHostFromIP(self, args=None):
        vals = {'s' : args['ip'], 'n' : '25'}
        id = self.getDeviceSearch(vals)['content'][0]['id']
        vals = {'d' : id, 't' : '3'}
        self.scanHost(vals)


    #Upload Threat List
    def addIPThreat(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/threatfeeds'
            payload = {'address':args['address'], 'addressType':'IP_ADDRESS', 'comment':args['comment']}
            r = self.s.request('POST', url, data=payload, verify=False)
        except:
            print "Could not add IP threat"
            sys.exit(0)

    def addDomainThreat(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/threatfeeds'
            payload = {'address':args['host'], 'addressType':'DOMAIN', 'comment':args['comment']} #Check address type
            r = self.s.request('POST', url, data=payload, verify=False)
        except:
             print "Could not add IP threat"
             sys.exit(0)

    def addSiteThreat(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/threatfeeds'
            payload = {'address':args['site'], 'addressType':'SITE', 'comment':args['comment']} #Check address type
            r = self.s.request('POST', url, data=payload, verify=False)
        except:
             print "Could not add IP threat"
             sys.exit(0)

    def addURLThreat(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/threatfeeds'
            payload = {'address':url, 'addressType':'URL', 'comment':args['comment']} #Check address type
            r = self.s.request('POST', url, data=payload, verify=False)
        except:
            print "Could not add IP threat"
            sys.exit(0)


    def toggleMD5(self, args=None):
        readdURL = 'https://' + self.ip + '/interface/rest/md5-threats/readd'
        wlurl = 'https://' + self.ip + '/interface/rest/md5-threats/whitelist'
        try:
            payload = {'id':args['name']}
            if args['wl'] == "True":
                r = self.s.request('POST', readdURL, data=payload, verify=False)
            else:
                r = self.s.request('POST', wlurl, data=payload, verify=False)
        except:
            print "Could not add IP threat"
            sys.exit(0)

    def undoAction(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/manualIncident/undoAction'
            payload = {'actionId':args['action'], 'password':self.loginParam['j_password']}
            r = self.s.request('POST', url, data=payload, verify=False)
        except:
            print "Could not undo action"
            sys.exit(0)

    def getIncidentOverview(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/incidents/pagedJson?endDate=' + str(args['smm']) + '%2F' + str(args['sdd']) + '%2F' + str(args['syyyy']) + '&mix=nonLearningModeOnly&namePattern=&page=0&size=' + str(args['n']) + \
                  '&sortCol=lastDetectedTimeStamp&sortDir=desc&startDate=' + str(args['mm']) + '%2F' + str(args['dd']) + '%2F' + str(args['yyyy'])
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get incident overview"
            sys.exit(0)

    #Gets Specific Incident Information
    def getSpecificIncident(self, args=None):
        try:
            incident = 'https://' + self.ip + '/interface/rest/incidents/json/details/' + str(args['n'])
            r = self.s.get(incident, verify=False)
            return r.json()
        except:
            print "Could not get specific incident"
            sys.exit(0)

    #Get DPI events
    def getDPIEvents(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/dpiEvents/pagedJson?endDate=12%2F17%2F2014&namePattern=&page=0&size=' + str(args['n']) + '&sortCol=timestamp&sortDir=desc&startDate=12%2F17%2F2014'
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get DPI events"
            sys.exit(0)

    #Gets Cybercon Level
    def getWarningLevel(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/app/status?skipPermissions=true'
            r = self.s.get(url, verify=False)
            print r.json()['cybercon']
            return r.json()['cybercon']
        except:
            print "Could not get warning level"
            return {"status" : "ERROR"}


    #Gets Devices
    def getDevices(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/devices/pagedJson?namePattern=&page=0&size=' + str(args['n']) + '&sortCol=ipV4Address&sortDir=asc'
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get devices"
            sys.exit(0)

    def getDeviceSearch(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/devices/pagedJson?namePattern=' + str(args['s']) + '&page=0&size=' + str(args['n']) + '&sortCol=ipV4Address&sortDir=asc'
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not perform device search"
            sys.exit(0)

    #Get Device Health
    def getDeviceHealth(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/heartbeats/json/all?namePattern=&page=0&size=' + str(args['n']) + '&sortCol=componentObject.name&sortDir=asc'
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get device health"
            sys.exit(0)

    #Get Audit Logs
    def getAuditTrail(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/audits/json?page=0&size=' + str(args['n']) + '&sortCol=timestamp&sortDir=desc'
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get audit trail"
            sys.exit(0)

    #Get General Threat Feed
    def getThreatFeeds(self, args=None):
        try:
            if args['t'] == 1:
                x = '&type=DOMAIN'
            elif args['t'] == 2:
                x = '&type=IP_ADDRESS'
            elif args['t'] == 3:
                x = '&type=URL'
            elif args['t'] == 4:
                x = '&type=SITE'
            else:
                x = ''

            url = 'https://' + self.ip + '/interface/rest/threatfeeds/pagedJson?namePattern=' + str(args['pattern']) + '&page=0&size=' + str(args['n']) + '&sortCol=address&sortDir=asc' + x
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get threat feeds"
            sys.exit(0)

    #Get General MD5 Feed
    def getMD5Feeds(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/md5-threats/pagedJson?namePattern=' + args['pattern'] + '&page=0&size=' + str(args['n']) + '&sortCol=md5&sortDir=asc'
            r = self.s.get(url, verify=False)
            print r.json()
            return r.json()
        except Exception as e:
            print e
            sys.exit(0)

    def getMD5(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/md5-threats/pagedJson?namePattern=' + str(args['md5']) + '&page=0&size=' + str(args['n']) + '&sortCol=md5&sortDir=asc'
            r = self.s.get(url, verify=False)

            val = r.json()
            print val
            print val["numberOfElements"]

            return val["numberOfElements"]

        except Exception as e:
            print e
            return {"status" : "Error getting MD5"}

    def getIPFeed(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/devices/pagedJson?namePattern=' + str(args['ip']) + '&page=0&size=' + str(args['n']) + '&sortCol=ipV4Address&sortDir=asc'
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get IP feeds"
            sys.exit(0)

    #Get Scan Types
    def getScanTypes(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/templates/json'
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get scan types"
            sys.exit(0)

    #Get Template Instances
    def getTemplateInstance(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/devices/' + str(args['device']) + '/templateInstances?size=' + str(args['n']) + '&templateId='
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get template instance"
            sys.exit(0)

    def getTemplateResults(self, args=None):
        try:
            url = 'https://' + self.ip + '/interface/rest/templateInstance/' + str(args['temp']) + '/registryList?diff_types=&name=' + str(args['s']) + '&page=0&size=' + str(args['n'])
            r = self.s.get(url, verify=False)
            return r.json()
        except:
            print "Could not get template results"
            sys.exit(0)