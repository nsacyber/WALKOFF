import xml.etree.cElementTree as et
import multiprocessing as mp
from multiprocessing import Value, Lock
import threading

import time

from core import workflow as wf
from core import config
from core.config import executionSettings


class Controller(object):
    def __init__(self):
        self.workflows = {}
        self.instances = {}
        self.tree = None

        self.mainProcess = None
        #self.lock = Lock()
        self.lock = threading.Lock()
        self.status = Value("i", 0)
        self.executionLog = mp.Queue()

    def loadWorkflowsFromFile(self, path):
        self.tree = et.ElementTree(file=path)
        for workflow in self.tree.iter(tag="workflow"):
            name = workflow.get("name")
            self.workflows[name] = wf.Workflow(name=name, workflowConfig=workflow)
        self.addChildWorkflows()

    def addChildWorkflows(self):
        for workflow in self.workflows:
            children = self.workflows[workflow].options.children
            for child in children:
                if child in self.workflows:
                    children[child] = self.workflows[child]

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

    # Main Processing Loop
    def mainLoop(self, status):
        queue = ["helloWorldWorkflow"]
        while self.status.value == 1:
            # Adds Ready Jobs to EventQueue
            # queue.addJobs(scheduler.readyPlays(playbook.plays))
            if len(queue) > 0:
                for job in queue:
                    pq = mp.Queue()
                    jobs = []
                    for process in range(0, executionSettings["maxJobs"]):
                        if len(queue) > 0:
                            # if job in queue execute
                            proc = self.workflows[queue.pop()].execute
                            #"start" - the entry id for the workflow execution
                            if proc:
                                worker = threading.Thread(target=proc, args=("start", pq))
                                jobs.append(worker)
                                worker.start()

                    for job in jobs:
                        t = pq.get()
                        self.executionLog.put(t)
                        job.join()

            else:
                # If no jobs then sleep for specified amount
                time.sleep(executionSettings["secondsDelay"])

        return None

    # Creates a thread and starts the Main Processing Loop
    def startActiveExecution(self):
        with self.lock:
            self.status.value = 1
        #self.mainProcess = mp.Process(target=self.mainLoop, args=(self.status.value,))
        self.mainProcess = threading.Thread(target=self.mainLoop, args=(self.status.value,))
        self.mainProcess.start()

    def stopActiveExecution(self):
        if self.mainProcess is not None:
            with self.lock:
                self.status.value = 0
            self.mainProcess = None
        else:
            print("No Process To Stop!")










