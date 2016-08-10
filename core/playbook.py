from multiprocessing import Queue

import json
import play

class Playbook:
    def __init__(self, path):
        self.plays = {}
        self.path = path
        with open(path) as f:
            self.playbook = json.load(f)
        for key in self.playbook:
            self.plays[key] = play.Play(key, self.playbook[key])

    def initPlays(self):
        for key in self.playbook:
            self.plays[key] = play.Play(key, self.playbook[key])

    def getPlay(self, key):
        if key in self.plays:
            return self.plays[key]

    def displayPlay(self, key):
        result = []
        if key in self.plays:
           for k, v in self.plays[key].steps.iteritems():
               result.append(v.getStepData())

        return result

    def displayPlayOptions(self, key):
        if key in self.plays:
            return self.plays[key].options

    def editPlayOptions(self, key, autorun=None, sDT=None, eDT=None, interval=None):
        if key in self.plays:
            if autorun != None:
                self.plays[key].options["autorun"] = autorun
            if sDT != None:
                self.plays[key].options["scheduler"]["sDT"] = sDT
            if eDT != None:
                self.plays[key].options["scheduler"]["eDT"] = eDT
            if interval != None:
                self.plays[key].options["scheduler"]["interval"] = interval

    def executePlay(self, key):
        if key in self.plays:
            pq = Queue()
            self.plays[key].executePlay(pq)
            return pq.get()

    def removePlay(self, key):
        if key in self.plays:
            print len(self.plays)
            del self.plays[key]
            print len(self.plays)
            return {"status" : "play removed"}
        else:
            return {"status" : "could not remove play"}

    def addEmptyPlay(self, key):
        template = json.loads('{"options" : {"autorun" : "true","scheduler" : {"sDT" : "2016-1-1 12:00:00","eDT" : "2016-1-1 12:00:00","interval" : "-1"}},"play" : []}')
        if key not in self.plays:
            self.playbook[key] = template
            data = self.playbook[key]
            self.plays[key] = play.Play(key, data)
            return {"status" : "added empty play"}
        else:
            return {"status" : "play already exists"}

    def updatePlaybook(self, path):
        with open(path) as f:
            self.playbook = json.load(f)

    def displayPlaybook(self):
        print "HERE"
        return self.playbook

    def generatePlaybook(self):
        result = {}
        for name in self.plays:
            result[name] = {}
            options = self.displayPlayOptions(name)
            play = self.displayPlay(name)

            if options != None:
                result[name]["options"] = options
            else:
                result[name]["options"] = {}

            if play != None:
                result[name]["play"] = play
            else:
                result[name]["play"] = []

        return result

    def revert(self):
        try:
            backupPath = "data/backup/playbook_backup.json"
            with open(backupPath, "r") as backupFile:
               open(self.path, "w").write(backupFile.read())
            return {"status" : "reverted configuration file to baseline"}
        except Exception as e:
            return {"status" : "could not revert configuration file", "error":e.message}
