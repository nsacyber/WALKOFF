import xml.etree.cElementTree as et
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from core import workflow as wf
from core import config

class Controller(object):
    def __init__(self):
        self.workflows = {}
        self.instances = {}
        self.tree = None

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(self.schedulerStatusListener,EVENT_SCHEDULER_START | EVENT_SCHEDULER_SHUTDOWN | EVENT_SCHEDULER_PAUSED | EVENT_SCHEDULER_RESUMED)
        self.scheduler.add_listener(self.jobStatusListener, EVENT_JOB_ADDED | EVENT_JOB_REMOVED)
        self.scheduler.add_listener(self.jobExecutionListener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.eventLog = []

    def loadWorkflowsFromFile(self, path):
        self.tree = et.ElementTree(file=path)
        for workflow in self.tree.iter(tag="workflow"):
            name = workflow.get("name")
            self.workflows[name] = wf.Workflow(name=name, workflowConfig=workflow)
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
        return steps, instances

    #Starts active execution
    def start(self):
        self.scheduler.start()

    #Stops active execution
    def stop(self):
        self.scheduler.shutdown()

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
        return self.scheduler.get_jobs()

    def jobExecutionListener(self, event):
        if event.exception:
            self.eventLog.append({"jobError": event.retval})
        else:
            self.eventLog.append({"jobExecuted":event.retval})

    def schedulerStatusListener(self, event):
        self.eventLog.append({"schedulerStatus" : event.code})

    def jobStatusListener(self, event):
        self.eventLog.append({"jobStatus" : event.code})














