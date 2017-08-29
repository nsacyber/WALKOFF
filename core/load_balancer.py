try:
    from Queue import Queue
except ImportError:
    from queue import Queue
import os
import gevent
import logging
import json
import zmq.green as zmq
from zmq.utils.strtypes import asbytes, cast_unicode
from core import workflow as wf
from core.case import callbacks
import signal

REQUESTS_ADDR = 'tcp://127.0.0.1:5555'
RESULTS_ADDR = 'tcp://127.0.0.1:5556'
COMM_ADDR = 'tcp://127.0.0.1:5557'

logger = logging.getLogger(__name__)


class LoadBalancer:
    def __init__(self):
        self.available_workers = []
        self.workflow_comms = {}
        self.thread_exit = False
        self.pending_workflows = Queue()
        self.ctx = zmq.Context.instance()

        self.request_socket = self.ctx.socket(zmq.ROUTER)
        self.request_socket.bind(REQUESTS_ADDR)

        self.comm_socket = self.ctx.socket(zmq.ROUTER)
        self.comm_socket.bind(COMM_ADDR)
        gevent.sleep(2)

    def manage_workflows(self):
        while True:
            if self.thread_exit:
                break
            # There is a worker available and a workflow in the queue, so pop it off and send it to the worker
            if self.available_workers and not self.pending_workflows.empty():
                workflow = self.pending_workflows.get()
                worker = self.available_workers.pop()
                self.workflow_comms[workflow['execution_uid']] = worker
                self.request_socket.send_multipart([worker, b"", asbytes(json.dumps(workflow))])
            # If there is a worker available but no pending workflows, then see if there are any other workers
            # available, but do not block in case a workflow becomes available
            else:
                try:
                    worker, empty, ready = self.request_socket.recv_multipart(flags=zmq.NOBLOCK)
                    if ready == b"Ready" or ready == b"Done":
                        self.available_workers.append(worker)
                except zmq.ZMQError:
                    gevent.sleep(0.1)
                    continue
        self.request_socket.close()
        self.comm_socket.close()
        self.ctx.destroy()
        return


class Worker:
    def __init__(self, id_):
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGQUIT, self.exit_handler)

        self.ctx = zmq.Context()

        self.request_sock = self.ctx.socket(zmq.REQ)
        self.request_sock.identity = u"Worker-{}".format(id_).encode("ascii")
        self.request_sock.connect(REQUESTS_ADDR)

        self.results_sock = self.ctx.socket(zmq.PUSH)
        self.results_sock.identity = u"Worker-{}".format(id_).encode("ascii")
        self.results_sock.connect(RESULTS_ADDR)

        self.comm_sock = self.ctx.socket(zmq.REQ)
        self.comm_sock.identity = u"Worker-{}".format(id_).encode("ascii")
        self.comm_sock.connect(COMM_ADDR)

        self.setup_worker_env()
        self.execute_workflow_worker()

    def exit_handler(self, signum, frame):
        if self.request_sock:
            self.request_sock.close()
        if self.results_sock:
            self.results_sock.close()
        if self.comm_sock:
            self.comm_sock.close()
        if self.ctx:
            self.ctx.destroy()
        os._exit(0)

    def setup_worker_env(self):
        import core.config.config
        core.config.config.initialize()

    def execute_workflow_worker(self):
        """Executes the workflow in a multi-threaded fashion.
        """
        self.request_sock.send(b"Ready")
        self.comm_sock.send(b"Executing")

        while True:
            workflow = self.request_sock.recv()

            workflow_json = json.loads(cast_unicode(workflow))

            uid = workflow_json['uid']
            del workflow_json['uid']
            execution_uid = workflow_json['execution_uid']
            del workflow_json['execution_uid']
            start = workflow_json['start']

            start_input = ''
            if 'start_input' in workflow_json:
                start_input = workflow_json['start_input']
                del workflow_json['start_input']

            workflow = wf.Workflow()
            workflow.from_json(workflow_json)
            workflow.uid = uid
            workflow.execution_uid = execution_uid
            workflow.start = start
            workflow.results_sock = self.results_sock
            workflow.comm_sock = self.comm_sock
            if 'breakpoint_steps' in workflow_json:
                workflow.breakpoint_steps = workflow_json['breakpoint_steps']

            workflow.execute(execution_uid=execution_uid, start=start, start_input=start_input)
            self.request_sock.send(b"Done")


class Receiver:
    def __init__(self):
        self.thread_exit = False
        self.workflows_executed = 0

        self.ctx = zmq.Context()
        self.results_sock = self.ctx.socket(zmq.PULL)
        self.results_sock.bind(RESULTS_ADDR)

    def send_callback(self, callback, sender, data):
        if 'data' in data:
            callback.send(sender, data=data['data'])
        else:
            callback.send(sender)

    def receive_results(self):
        while True:
            if self.thread_exit:
                break
            try:
                message = self.results_sock.recv_json(zmq.NOBLOCK)
            except zmq.ZMQError:
                gevent.sleep(0.1)
                continue

            callback = message['callback_name']
            sender = message['sender']
            data = message

            if callback == "Workflow Execution Start":
                self.send_callback(callbacks.WorkflowExecutionStart, sender, data)
            elif callback == "Next Step Found":
                self.send_callback(callbacks.NextStepFound, sender, data)
            elif callback == "App Instance Created":
                self.send_callback(callbacks.AppInstanceCreated, sender, data)
            elif callback == "Workflow Shutdown":
                self.send_callback(callbacks.WorkflowShutdown, sender, data)
                self.workflows_executed += 1
            elif callback == "Workflow Input Validated":
                self.send_callback(callbacks.WorkflowInputValidated, sender, data)
            elif callback == "Workflow Input Invalid":
                self.send_callback(callbacks.WorkflowInputInvalid, sender, data)
            elif callback == "Workflow Paused":
                self.send_callback(callbacks.WorkflowPaused, sender, data)
            elif callback == "Workflow Resumed":
                self.send_callback(callbacks.WorkflowResumed, sender, data)
            elif callback == "Step Execution Success":
                self.send_callback(callbacks.StepExecutionSuccess, sender, data)
            elif callback == "Step Execution Error":
                self.send_callback(callbacks.StepExecutionError, sender, data)
            elif callback == "Step Input Validated":
                self.send_callback(callbacks.StepInputValidated, sender, data)
            elif callback == "Function Execution Success":
                self.send_callback(callbacks.FunctionExecutionSuccess, sender, data)
            elif callback == "Step Input Invalid":
                self.send_callback(callbacks.StepInputInvalid, sender, data)
            elif callback == "Conditionals Executed":
                self.send_callback(callbacks.ConditionalsExecuted, sender, data)
            elif callback == "Next Step Taken":
                self.send_callback(callbacks.NextStepTaken, sender, {})
            elif callback == "Next Step Not Taken":
                self.send_callback(callbacks.NextStepNotTaken, sender, {})
            elif callback == "Flag Success":
                self.send_callback(callbacks.FlagSuccess, sender, {})
            elif callback == "Flag Error":
                self.send_callback(callbacks.FlagError, sender, {})
            elif callback == "Filter Success":
                self.send_callback(callbacks.FilterSuccess, sender, {})
            elif callback == "Filter Error":
                self.send_callback(callbacks.FilterError, sender, {})

        self.results_sock.close()
        self.ctx.destroy()
        return
