class eventQueue():
    def __init__(self, data=[]):
        self.queue = data

    def addJob(self, play=None):
        if play != None:
            self.queue.append(play)

    def addJobs(self, plays=[]):
        self.queue += plays

    def getQueue(self):
        return self.queue