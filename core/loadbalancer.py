import os
import gevent
import logging
import json
import zmq.green as zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
from zmq.utils.strtypes import asbytes, cast_unicode
from core import workflow as wf
from core.case import callbacks
import signal
import core.config.paths
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

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
        self.auth = ThreadAuthenticator(self.ctx)
        self.auth.start()
        self.auth.allow('127.0.0.1')
        self.auth.configure_curve(domain='*', location=core.config.paths.zmq_public_keys_path)
        server_secret_file = os.path.join(core.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = zmq.auth.load_certificate(server_secret_file)

        self.request_socket = self.ctx.socket(zmq.ROUTER)
        self.request_socket.curve_secretkey = server_secret
        self.request_socket.curve_publickey = server_public
        self.request_socket.curve_server = True
        self.request_socket.bind(REQUESTS_ADDR)

        self.comm_socket = self.ctx.socket(zmq.ROUTER)
        self.comm_socket.curve_secretkey = server_secret
        self.comm_socket.curve_publickey = server_public
        self.comm_socket.curve_server = True
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
        self.auth.stop()
        self.ctx.destroy()
        return


class Worker:
    def __init__(self, id_):
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGQUIT, self.exit_handler)

        server_secret_file = os.path.join(core.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = zmq.auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(core.config.paths.zmq_private_keys_path, "client.key_secret")
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)

        self.ctx = zmq.Context.instance()
        self.auth = ThreadAuthenticator(self.ctx)
        self.auth.start()
        self.auth.allow('127.0.0.1')
        self.auth.configure_curve(domain='*', location=core.config.paths.zmq_public_keys_path)

        self.results_sock = self.ctx.socket(zmq.PUSH)
        self.results_sock.identity = u"Worker-{}".format(id_).encode("ascii")
        self.results_sock.curve_secretkey = server_secret
        self.results_sock.curve_publickey = server_public
        self.results_sock.curve_server = True
        self.results_sock.connect(RESULTS_ADDR)

        self.request_sock = self.ctx.socket(zmq.REQ)
        self.request_sock.identity = u"Worker-{}".format(id_).encode("ascii")
        self.request_sock.curve_secretkey = client_secret
        self.request_sock.curve_publickey = client_public
        self.request_sock.curve_serverkey = server_public
        self.request_sock.connect(REQUESTS_ADDR)

        self.comm_sock = self.ctx.socket(zmq.REQ)
        self.comm_sock.identity = u"Worker-{}".format(id_).encode("ascii")
        self.comm_sock.curve_secretkey = client_secret
        self.comm_sock.curve_publickey = client_public
        self.comm_sock.curve_serverkey = server_public
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
        if self.auth:
            self.auth.stop()
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
    callback_lookup = {
        'Workflow Execution Start': (callbacks.WorkflowExecutionStart, True),
        'Next Step Found': (callbacks.NextStepFound, True),
        'App Instance Created': (callbacks.AppInstanceCreated, True),
        'Workflow Shutdown': (callbacks.WorkflowShutdown, True),
        'Workflow Input Validated': (callbacks.WorkflowInputInvalid, True),
        'Workflow Paused': (callbacks.WorkflowPaused, True),
        'Workflow Resumed': (callbacks.WorkflowResumed, True),
        'Step Execution Success': (callbacks.StepExecutionSuccess, True),
        'Step Execution Error': (callbacks.StepExecutionError, True),
        'Step Started': (callbacks.StepStarted, True),
        'Function Execution Success': (callbacks.FunctionExecutionSuccess, True),
        'Step Input Invalid': (callbacks.StepInputInvalid, True),
        'Conditionals Executed': (callbacks.ConditionalsExecuted, True),
        'Next Step Taken': (callbacks.NextStepTaken, False),
        'Next Step Not Taken': (callbacks.NextStepNotTaken, False),
        'Flag Success': (callbacks.FlagSuccess, False),
        'Flag Error': (callbacks.FlagError, False),
        'Filter Success': (callbacks.FilterSuccess, False),
        'Filter Error': (callbacks.FilterError, False)}

    def __init__(self):
        self.thread_exit = False
        self.workflows_executed = 0

        client_secret_file = os.path.join(core.config.paths.zmq_private_keys_path, "client.key_secret")
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
        server_public_file = os.path.join(core.config.paths.zmq_public_keys_path, "server.key")
        server_public, _ = zmq.auth.load_certificate(server_public_file)

        self.ctx = zmq.Context()
        self.results_sock = self.ctx.socket(zmq.PULL)
        self.results_sock.curve_secretkey = client_secret
        self.results_sock.curve_publickey = client_public
        self.results_sock.curve_serverkey = server_public
        self.results_sock.bind(RESULTS_ADDR)

    @staticmethod
    def send_callback(callback, sender, data):
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

            callback_name = message['callback_name']
            sender = message['sender']
            data = message
            try:
                callback = self.callback_lookup[callback_name]
                data = data if callback[1] else {}
                Receiver.send_callback(callback[0], sender, data)
            except KeyError:
                logger.error('Unknown callabck sent {}'.format(callback_name))
            else:
                if callback_name == 'Workflow Shutdown':
                    self.workflows_executed += 1

        self.results_sock.close()
        self.ctx.destroy()
        return
