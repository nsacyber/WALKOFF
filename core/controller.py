import xml.etree.cElementTree as et
from os import sep
import os

import time

from collections import namedtuple
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from apscheduler.schedulers.gevent import GeventScheduler

from core import config
from core import workflow as wf
from core.case import callbacks
from core.events import EventListener
from core.helpers import locate_workflows_in_directory, construct_workflow_name_key, extract_workflow_name

from gevent import monkey

import multiprocessing
import dill

monkey.patch_all(thread=False, socket=False)

NUM_PROCESSES = 2
queue = None
pool = None
results = {}

_WorkflowKey = namedtuple('WorkflowKey', ['playbook', 'workflow'])

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

        initialize_threading()

    def loadWorkflowsFromFile(self, path, name_override=None, playbook_override=None):
        self.tree = et.ElementTree(file=path)
        playbook_name = playbook_override if playbook_override else os.path.splitext(os.path.basename(path))[0]
        for workflow in self.tree.iter(tag='workflow'):
            workflow_name = name_override if name_override else workflow.get('name')
            name = construct_workflow_name_key(playbook_name, workflow_name)
            key = _WorkflowKey(playbook_name, workflow_name)
            self.workflows[key] = wf.Workflow(name=name,
                                              workflowConfig=workflow,
                                              parent_name=self.name,
                                              filename=playbook_name)
        self.addChildWorkflows()
        self.addWorkflowScheduledJobs()

    def load_all_workflows_from_directory(self, path=config.workflowsPath):
        for workflow in locate_workflows_in_directory(path):
            self.loadWorkflowsFromFile(os.path.join(config.workflowsPath, workflow))

    def addChildWorkflows(self):
        for workflow in self.workflows:
            playbook_name = workflow.playbook
            children = self.workflows[workflow].options.children
            for child in children:
                workflow_key = _WorkflowKey(playbook_name, extract_workflow_name(child, playbook_name=playbook_name))
                if workflow_key in self.workflows:
                    children[child] = self.workflows[workflow_key]

    def addWorkflowScheduledJobs(self):
        for workflow in self.workflows:
            if (self.workflows[workflow].options.enabled
                    and self.workflows[workflow].options.scheduler["autorun"] == "true"):
                schedule_type = self.workflows[workflow].options.scheduler["type"]
                schedule = self.workflows[workflow].options.scheduler["args"]
                self.scheduler.add_job(self.workflows[workflow].execute, trigger=schedule_type, replace_existing=True,
                                       **schedule)

    def create_workflow_from_template(self,
                                      playbook_name,
                                      workflow_name,
                                      template_playbook='emptyWorkflow',
                                      template_name='emptyWorkflow'):
        path = '{0}{1}{2}.workflow'.format(config.templatesPath, sep, template_playbook)
        return self.load_workflow_from_file(path=path,
                                            workflow_name=template_name,
                                            name_override=workflow_name,
                                            playbook_override=playbook_name)

    def create_playbook_from_template(self, playbook_name,
                                      template_playbook='emptyWorkflow'):
        #TODO: Need a handler for returning workflow key and status
        path = '{0}{1}{2}.workflow'.format(config.templatesPath, sep, template_playbook)
        self.loadWorkflowsFromFile(path=path, playbook_override=playbook_name)

    def removeWorkflow(self, playbook_name, workflow_name):
        name = _WorkflowKey(playbook_name, workflow_name)
        if name in self.workflows:
            del self.workflows[name]
            return True
        return False

    def remove_playbook(self, playbook_name):
        for name in [workflow for workflow in self.workflows if workflow.playbook == playbook_name]:
            del self.workflows[name]
            return True
        return False

    def get_all_workflows(self):
        result = {}
        for key in self.workflows.keys():
            if key.playbook not in result:
                result[key.playbook] = []
            result[key.playbook].append(key.workflow)
        return result

    def is_workflow_registered(self, playbook_name, workflow_name):
        return _WorkflowKey(playbook_name, workflow_name) in self.workflows

    def is_playbook_registerd(self, playbook_name):
        return any(workflow_key.playbook == playbook_name for workflow_key in self.workflows)

    def update_workflow_name(self, old_playbook, old_workflow, new_playbook, new_workflow):
        old_key = _WorkflowKey(old_playbook, old_workflow)
        new_key = _WorkflowKey(new_playbook, new_workflow)
        self.workflows[new_key] = self.workflows.pop(old_key)
        self.workflows[new_key].name = construct_workflow_name_key(new_playbook, new_workflow)

    def update_playbook_name(self, old_playbook, new_playbook):
        for key in [name for name in self.workflows.keys() if name.playbook == old_playbook]:
            self.update_workflow_name(old_playbook, key.workflow, new_playbook, key.workflow)

    # def executeWorkflowWorker(self):
    #
    #     print("Thread " + str(os.getpid()) + " starting up...")
    #
    #     while (True):
    #         while (self.queue.empty()):
    #             continue
    #         name,start,data = self.queue.get()
    #         print("Thread " + str(os.getpid()) + " received and executing workflow "+name)
    #         steps, instances = self.workflows[name].execute(start=start, data=data)

    def executeWorkflow(self, playbook_name, workflow_name, start="start", data=None):
        global queue
        print("Boss thread putting " + workflow_name + " workflow on queue...:")
        # self.workflows[_WorkflowKey(playbook_name, workflow_name)].execute(start=start, data=data)
        workFl = self.workflows[_WorkflowKey(playbook_name, workflow_name)]
        # CAN'T PICKLE STEPS (conditionals, errors -- both nextStep objects (eventHandler)), OPTIONS (children (tieredWorkflow-childWorkflow))
        #pickled_workflow = dill.dumps(workFl)
        #queue.put((pickled_workflow, start, data))
        #self.jobExecutionListener.execute_event_code(self, 'JobExecuted')

    def get_workflow(self, playbook_name, workflow_name):
        key = _WorkflowKey(playbook_name, workflow_name)
        if key in self.workflows:
            return self.workflows[key]
        return None

    def playbook_to_xml(self, playbook_name):
        workflows = [workflow for key, workflow in self.workflows.items() if key.playbook == playbook_name]
        if workflows:
            xml = et.Element("workflows")
            for workflow in workflows:
                xml.append(workflow.to_xml())
            return xml
        else:
            return None

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
