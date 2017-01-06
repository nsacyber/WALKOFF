import xml.etree.cElementTree as et
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED

from blinker import Signal
from core import workflow as wf
from core import config, case

class Controller(object):
    def __init__(self, name="defaultController"):
        self.name = name
        self.workflows = {}
        self.instances = {}
        self.tree = None

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(self.schedulerStatusListener,EVENT_SCHEDULER_START | EVENT_SCHEDULER_SHUTDOWN | EVENT_SCHEDULER_PAUSED | EVENT_SCHEDULER_RESUMED)
        self.scheduler.add_listener(self.jobStatusListener, EVENT_JOB_ADDED | EVENT_JOB_REMOVED)
        self.scheduler.add_listener(self.jobExecutionListener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.eventLog = []


        #Signals
        self.schedulerStart = Signal()
        self.schedulerStart.connect(case.schedulerStart)

        self.schedulerShutdown = Signal()
        self.schedulerShutdown.connect(case.schedulerShutdown)

        self.schedulerPaused = Signal()
        self.schedulerPaused.connect(case.schedulerPaused)

        self.schedulerResumed = Signal()
        self.schedulerResumed.connect(case.schedulerResumed)

        self.jobAdded = Signal()
        self.jobAdded.connect(case.jobAdded)

        self.jobRemoved = Signal()
        self.jobRemoved.connect(case.jobRemoved)

        self.jobExecuted = Signal()
        self.jobExecuted.connect(case.jobExecuted)

        self.jobException = Signal()
        self.jobException.connect(case.jobException)

    def loadWorkflowsFromFile(self, path):
        self.tree = et.ElementTree(file=path)
        for workflow in self.tree.iter(tag="workflow"):
            name = workflow.get("name")
            self.workflows[name] = wf.Workflow(name=name, workflowConfig=workflow, parentController=self.name)
        self.addChildWorkflows()
        self.addWorkflowScheduledJobs()

    def addChildWorkflows(self):
        for workflow in self.workflows:
            children = self.workflows[workflow].options.children
            for child in children:
                if child in self.workflows:
                    children[child] = self.workflows[child]

    def addWorkflowScheduledJobs(self):
        for workflow in self.workflows:
            if self.workflows[workflow].options.enabled and self.workflows[workflow].options.scheduler["autorun"] == "true":
                scheduleType = self.workflows[workflow].options.scheduler["type"]
                schedule = self.workflows[workflow].options.scheduler["args"]
                self.scheduler.add_job(self.workflows[workflow].execute, trigger=scheduleType, replace_existing=True, **schedule)

    def createWorkflowFromTemplate(self, name="emptyWorkflow"):
        self.loadWorkflowsFromFile(path = config.templatesPath + name + ".workflow")

    def removeWorkflow(self, name=""):
        if name in self.workflows:
            del self.workflows[name]
            return True
        return False

    def updateWorkflowName(self, oldName="", newName=""):
        self.workflows[newName] = self.workflows.pop(oldName)
        self.workflows[newName].name = newName

    def executeWorkflow(self, name, start="start"):
        steps, instances = self.workflows[name].execute(start=start)
        self.jobExecuted.send(self)
        return steps, instances

    #Starts active execution
    def start(self):
        self.scheduler.start()

    #Stops active execution
    def stop(self, wait=True):
        self.scheduler.shutdown(wait=wait)

    #Pauses active execution
    def pause(self):
        self.scheduler.pause()

    #Resumes active execution
    def resume(self):
        self.scheduler.resume()

    #Pauses active execution of specific job
    def pauseJob(self, jobId):
        self.scheduler.pause_job(job_id=jobId)

    #Resumes active execution of specific job
    def resumeJob(self, jobId):
        self.scheduler.resume_job(job_id=jobId)

    #Returns jobs scheduled for active execution
    def getScheduledJobs(self):
        self.scheduler.get_jobs()


    def jobExecutionListener(self, event):
        if event.exception:
            self.jobException.send(self)
            self.eventLog.append({"jobError": event.retval})
        else:
            self.jobExecuted.send(self)
            self.eventLog.append({"jobExecuted":event.retval})

    def schedulerStatusListener(self, event):
        if event.code == 1:
            self.schedulerStart.send(self)
        elif event.code == 2:
            self.schedulerShutdown.send(self)
        elif event.code == 4:
            self.schedulerPaused.send(self)
        elif event.code == 8:
            self.schedulerResumed.send(self)
        self.eventLog.append({"schedulerStatus" : event.code})

    def jobStatusListener(self, event):
        if event.code == 512:
            self.jobAdded.send(self)
        elif event.code == 1024:
            self.jobRemoved.send(self)

        self.eventLog.append({"jobStatus" : event.code})














