import xml.etree.cElementTree as et
from os import sep
import os

import time

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from apscheduler.schedulers.gevent import GeventScheduler

from core import config
from core.workflow import Workflow
from core.case import callbacks
from core.events import EventListener
from core.helpers import locate_workflows_in_directory

import multiprocessing
import dill

NUM_PROCESSES = 2
queue = None
pool = None
results = {}

def initialize_threading():
    global queue
    global pool
    global results

    manager = multiprocessing.Manager()
    queue = manager.Queue()

    print("Initializing thread pool...")
    pool = multiprocessing.Pool(processes=NUM_PROCESSES)
    print("Initialized pool.")
    for i in range(0, NUM_PROCESSES):
        results[i] = pool.apply_async(executeWorkflowWorker, (queue,))
    print("Initialized")

def shutdown_pool():
    global pool
    global results
    global queue

    # for i in range(0, NUM_PROCESSES):
    #     while (results[i].ready() is not True):
    #         continue

    time.sleep(2)

    pool.terminate()

def executeWorkflowWorker(queue):

    print("Thread " + str(os.getpid()) + " starting up...")

    while (True):
        #while (queue.empty()):
        #    continue
        print("Thread waiting...")
        pickled_workflow,start,data = queue.get(block=True)
        print("Thread popped something off")
        workflow = dill.loads(pickled_workflow)
        #print("Thread " + str(os.getpid()) + " received and executing workflow "+workflow.get("name"))
        #steps, instances = workflow.execute(start=start, data=data)

class SchedulerStatusListener(EventListener):
    def __init__(self, shared_log=None):
        EventListener.__init__(self, "schedulerStatus", shared_log=shared_log,
                               events={EVENT_SCHEDULER_START: callbacks.add_system_entry("Scheduler start"),
                                       EVENT_SCHEDULER_SHUTDOWN: callbacks.add_system_entry("Scheduler shutdown"),
                                       EVENT_SCHEDULER_PAUSED: callbacks.add_system_entry("Scheduler paused"),
                                       EVENT_SCHEDULER_RESUMED: callbacks.add_system_entry("Scheduler resumed")})


class JobStatusListener(EventListener):
    def __init__(self, shared_log=None):
        EventListener.__init__(self, "jobStatus", shared_log,
                               events={EVENT_JOB_ADDED: callbacks.add_system_entry("Job added"),
                                       EVENT_JOB_REMOVED: callbacks.add_system_entry("Job removed")})


class JobExecutionListener(EventListener):
    def __init__(self, shared_log=None):
        EventListener.__init__(self, "jobExecution", shared_log,
                               events={'JobExecuted': callbacks.add_system_entry("Job executed"),
                                       'JobError': callbacks.add_system_entry("Job executed with error")})

    def execute_event(self, sender, event, data=''):
        if event.exception:
            self.events['JobError'].send(sender, data)
            self.eventlog.append({"jobError": event.retval})
        else:
            self.events['JobExecuted'].send(sender)
            self.eventlog.append({"jobExecuted": event.retval})

    def execute_event_code(self, sender, event_code, data=''):
        if event_code == 'JobExecuted':
            self.events[event_code].send(sender, data)
            self.eventlog.append({"jobExecuted": 'Success'})
        elif event_code == 'JobError':
            self.events[event_code].send(sender, data)
            self.eventlog.append({"jobError": 'Error'})
        else:
            self.eventlog.append({event_code: 'Unsupported!'})

    def callback(self, sender):
        def execution(event):
            self.execute_event(sender, event)

        return execution

class Controller(object):

    def __init__(self, name="defaultController"):
        self.name = name
        self.workflows = {}
        self.load_all_workflows_from_directory()
        self.instances = {}
        self.tree = None
        self.eventlog = []
        self.schedulerStatusListener = SchedulerStatusListener(self.eventlog)
        self.jobStatusListener = JobStatusListener(self.eventlog)
        self.jobExecutionListener = JobExecutionListener(self.eventlog)
        self.scheduler = GeventScheduler()
        self.scheduler.add_listener(self.schedulerStatusListener.callback(self),
                                    EVENT_SCHEDULER_START | EVENT_SCHEDULER_SHUTDOWN
                                    | EVENT_SCHEDULER_PAUSED | EVENT_SCHEDULER_RESUMED)
        self.scheduler.add_listener(self.jobStatusListener.callback(self), EVENT_JOB_ADDED | EVENT_JOB_REMOVED)
        self.scheduler.add_listener(self.jobExecutionListener.callback(self), EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.ancestry = [self.name]

    def loadWorkflowsFromFile(self, path, name_override=None):
        self.tree = et.ElementTree(file=path)
        for workflow in self.tree.iter(tag="workflow"):
            name = name_override if name_override else workflow.get("name")
            self.workflows[name] = Workflow(name=name, workflowConfig=workflow, parent_name=self.name)
        self.addChildWorkflows()
        self.addWorkflowScheduledJobs()

    def load_all_workflows_from_directory(self, path=config.workflowsPath):
        for workflow in locate_workflows_in_directory():
            self.loadWorkflowsFromFile(os.path.join(config.workflowsPath, workflow))

    def addChildWorkflows(self):
        for workflow in self.workflows:
            children = self.workflows[workflow].options.children
            for child in children:
                if child in self.workflows:
                    children[child] = self.workflows[child]

    def addWorkflowScheduledJobs(self):
        for workflow in self.workflows:
            if (self.workflows[workflow].options.enabled
                    and self.workflows[workflow].options.scheduler["autorun"] == "true"):
                schedule_type = self.workflows[workflow].options.scheduler["type"]
                schedule = self.workflows[workflow].options.scheduler["args"]
                self.scheduler.add_job(self.workflows[workflow].execute, trigger=schedule_type, replace_existing=True,
                                       **schedule)

    def create_workflow_from_template(self, template_name="emptyWorkflow", workflow_name=None):
        self.loadWorkflowsFromFile(path=config.templatesPath + sep + template_name + ".workflow",
                                   name_override=workflow_name)

    def removeWorkflow(self, name=""):
        if name in self.workflows:
            del self.workflows[name]
            return True
        return False

    def updateWorkflowName(self, oldName="", newName=""):
        self.workflows[newName] = self.workflows.pop(oldName)
        self.workflows[newName].name = newName

    def executeWorkflow(self, name, start="start", data=None):
        global queue
        #self.workflows[name].execute(start=start, data=data)
        print("Boss thread putting "+name+" workflow on queue...:")
        workFl = self.workflows[name]
        for k, v in workFl.steps.items():
            #print(k)
            # print()
            # for a, b in v.__dict__.items():
            #     print(a)
            #     if (a == "event_handler"):
            #         for c,d in b.__dict__.items():
            #             print (c)
            #             for e, f in d.items():
            #                 print(e)
            #                 for g, h in f.__dict__.items():
            #                     print(g)
            #                     dill.dumps(h)
            #                 dill.dumps(f)
            #             dill.dumps(d)
            #     dill.dumps(b)
            # dill.dumps(v)
            workFl.steps[k].rawXML = str(workFl.steps[k].rawXML)
        workFl.workflowXML = str(workFl.workflowXML)
        pickled_workflow = dill.dumps(workFl)
        queue.put((pickled_workflow, start, data))
        #self.jobExecutionListener.execute_event_code(self, 'JobExecuted')

    # Starts active execution
    def start(self):
        self.scheduler.start()

    # Stops active execution
    def stop(self, wait=True):
        self.scheduler.shutdown(wait=wait)

    # Pauses active execution
    def pause(self):
        self.scheduler.pause()

    # Resumes active execution
    def resume(self):
        self.scheduler.resume()

    # Pauses active execution of specific job
    def pauseJob(self, job_id):
        self.scheduler.pause_job(job_id=job_id)

    # Resumes active execution of specific job
    def resumeJob(self, job_id):
        self.scheduler.resume_job(job_id=job_id)

    # Returns jobs scheduled for active execution
    def getScheduledJobs(self):
        self.scheduler.get_jobs()


controller = Controller()
