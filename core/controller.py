import xml.etree.cElementTree as et
from os import sep
import os

import time

from collections import namedtuple

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from apscheduler.schedulers.tornado import TornadoScheduler

from core.config import paths
from core import workflow as wf
from core.case import subscription
from core.case import callbacks
from core.helpers import locate_workflows_in_directory, construct_workflow_name_key, extract_workflow_name

from multiprocessing import Pool
from multiprocessing import Manager
import dill
from copy import deepcopy

NUM_PROCESSES = 2
threads = []

_WorkflowKey = namedtuple('WorkflowKey', ['playbook', 'workflow'])

def initialize_threading():
    global queue
    global pool

    manager = Manager()
    queue = manager.Queue()

    print("Initializing thread pool...")
    pool = Pool(processes=NUM_PROCESSES)
    print("Initialized pool.")
    for i in range(0, NUM_PROCESSES):
        pool.apply_async(executeWorkflowWorker, (queue,))
    # print("Initialized")
    #dill.settings["byref"] = True

def shutdown_pool():
    global pool

    #pool.join()

#def executeWorkflowWorker(queue, subs):
def executeWorkflowWorker(queue):
    #subscription.set_subscriptions(subs)

    print("Thread " + str(os.getpid()) + " starting up...")

    while (True):
        while not queue.empty():
            print("Queue not empty...trying to pop")
            pickled_workflow,start,data,subs = queue.get()
            print("popped!")
            subscription.set_subscriptions(subs)
            workflow = dill.loads(pickled_workflow) #this line takes forever...can we use something like json instead?
            #print("Thread popped "+workflow.filename+" off queue...")
            print(workflow.filename)
            #print("Thread " + str(os.getpid()) + " received and executing workflow "+workflow.get("name"))
            workflow.execute(start=start, data=data)
            workflow.is_completed = True
            print(workflow.is_completed)
            print("done")

# def executeWorkflowWorker(workflow, start, data):
#     #global queue
#
#     print("Thread " + str(os.getpid()) + " starting up...")
#
#     #workflow = dill.loads(pickled_workflow)
#
#     print("Thread executing "+workflow.filename+"...")
#
#     workflow.execute(start=start, data=data)
#
#     # while (True):
#     #     while not queue.empty():
#     #         print("Queue not empty...trying to pop")
#     #         pickled_workflow,start,data = queue.get()
#     #         workflow = dill.loads(pickled_workflow)
#     #         print("Thread popped "+workflow.filename+" off queue...")
#         # pickled_workflow,start,data = queue.get(block=True)
#         # workflow = dill.loads(pickled_workflow)
#         #print("Thread " + str(os.getpid()) + " received and executing workflow "+workflow.get("name"))
#         #steps, instances = workflow.execute(start=start, data=data)

class Controller(object):

    def __init__(self, name="defaultController", appPath=None):
        self.name = name
        self.workflows = {}
        self.load_all_workflows_from_directory(path=appPath)
        self.instances = {}
        self.tree = None

        self.scheduler = TornadoScheduler()
        self.scheduler.add_listener(self.__scheduler_listener(),
                                    EVENT_SCHEDULER_START | EVENT_SCHEDULER_SHUTDOWN
                                    | EVENT_SCHEDULER_PAUSED | EVENT_SCHEDULER_RESUMED
                                    | EVENT_JOB_ADDED | EVENT_JOB_REMOVED
                                    | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.ancestry = [self.name]

        #initialize_threading()

    def load_workflow_from_file(self, path, workflow_name, name_override=None, playbook_override=None):
        self.tree = et.ElementTree(file=path)
        playbook_name = playbook_override if playbook_override else os.path.splitext(os.path.basename(path))[0]
        for workflow in self.tree.iter(tag="workflow"):
            current_workflow_name = workflow.get('name')
            if current_workflow_name == workflow_name:
                if name_override:
                    workflow_name = name_override
                name = construct_workflow_name_key(playbook_name, workflow_name)
                key = _WorkflowKey(playbook_name, workflow_name)
                self.workflows[key] = wf.Workflow(name=name,
                                                  workflowConfig=workflow,
                                                  parent_name=self.name,
                                                  filename=playbook_name)
                break
        else:
            return False

        self.addChildWorkflows()
        self.addWorkflowScheduledJobs()
        return True

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

    def load_all_workflows_from_directory(self, path=paths.workflows_path):
        if not path:
            path = paths.workflows_path
        for workflow in locate_workflows_in_directory(path):
            self.loadWorkflowsFromFile(os.path.join(path, workflow))

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
        path = '{0}{1}{2}.workflow'.format(paths.templates_path, sep, template_playbook)
        return self.load_workflow_from_file(path=path,
                                            workflow_name=template_name,
                                            name_override=workflow_name,
                                            playbook_override=playbook_name)

    def create_playbook_from_template(self, playbook_name,
                                      template_playbook='emptyWorkflow'):
        #TODO: Need a handler for returning workflow key and status
        path = '{0}{1}{2}.workflow'.format(paths.templates_path, sep, template_playbook)
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

    # def executeWorkflowWorker(self, workflow, start, data, subs):
    #     # global queue
    #
    #     #print(id(subscription.subscriptions))
    #     subscription.set_subscriptions(subs)
    #
    #     print("Thread " + str(os.getpid()) + " starting up...")
    #
    #     # workflow = dill.loads(pickled_workflow)
    #
    #     print("Thread executing " + workflow.filename + "...")
    #
    #     workflow.execute(start=start, data=data)
    #
    #     self.jobExecutionListener.execute_event_code(self, 'JobExecuted')
    #
    #     workflow.is_completed = True
    #
    #     # from core.case.database import case_db, Event
    #     # print(case_db.session.query(Event).all())
    #
    #     # while (True):
    #     #     while not queue.empty():
    #     #         print("Queue not empty...trying to pop")
    #     #         pickled_workflow,start,data = queue.get()
    #     #         workflow = dill.loads(pickled_workflow)
    #     #         print("Thread popped "+workflow.filename+" off queue...")
    #     # pickled_workflow,start,data = queue.get(block=True)
    #     # workflow = dill.loads(pickled_workflow)
    #     # print("Thread " + str(os.getpid()) + " received and executing workflow "+workflow.get("name"))
    #     # steps, instances = workflow.execute(start=start, data=data)

    def executeWorkflow(self, playbook_name, workflow_name, start="start", data=None):
        global queue

        print("Boss thread putting " + workflow_name + " workflow on queue...:")
        # self.workflows[_WorkflowKey(playbook_name, workflow_name)].execute(start=start, data=data)
        key = _WorkflowKey(playbook_name, workflow_name)
        workFl = self.workflows[key]
        # CAN'T PICKLE STEPS (conditionals, errors -- both nextStep objects (eventHandler)), OPTIONS (children (tieredWorkflow-childWorkflow))
        #pool.apply(executeWorkflowWorker, (workFl, start, data))
        #workFl.event_handler = None
        #workFl.options = None
        #workFl.steps = None
        pickled_workflow = dill.dumps(workFl)
        subs = deepcopy(subscription.subscriptions)
        queue.put((pickled_workflow, start, data, subs))
        #callbacks.SchedulerJobExecuted.send(self)

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
        return self.scheduler.state


    # Stops active execution
    def stop(self, wait=True):
        self.scheduler.shutdown(wait=wait)
        return self.scheduler.state


    # Pauses active execution
    def pause(self):
        self.scheduler.pause()
        return self.scheduler.state

    # Resumes active execution
    def resume(self):
        self.scheduler.resume()
        return self.scheduler.state

    # Pauses active execution of specific job
    def pauseJob(self, job_id):
        self.scheduler.pause_job(job_id=job_id)

    # Resumes active execution of specific job
    def resumeJob(self, job_id):
        self.scheduler.resume_job(job_id=job_id)

    # Returns jobs scheduled for active execution
    def getScheduledJobs(self):
        self.scheduler.get_jobs()

    def __scheduler_listener(self):
        event_selector_map = {EVENT_SCHEDULER_START: (lambda: callbacks.SchedulerStart.send(self)),
                              EVENT_SCHEDULER_SHUTDOWN: (lambda: callbacks.SchedulerShutdown.send(self)),
                              EVENT_SCHEDULER_PAUSED: (lambda: callbacks.SchedulerPaused.send(self)),
                              EVENT_SCHEDULER_RESUMED: (lambda: callbacks.SchedulerResumed.send(self)),
                              EVENT_JOB_ADDED: (lambda: callbacks.SchedulerJobAdded.send(self)),
                              EVENT_JOB_REMOVED: (lambda: callbacks.SchedulerJobRemoved.send(self)),
                              EVENT_JOB_EXECUTED: (lambda: callbacks.SchedulerJobExecuted.send(self)),
                              EVENT_JOB_ERROR: (lambda: callbacks.SchedulerJobError.send(self))}

        def event_selector(event):
            try:
                event_selector_map[event.code]()
            except KeyError:
                print("Error: Unknown event sent!")

        return event_selector

controller = Controller()
