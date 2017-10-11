import os
import gevent
import logging
import json
import zmq.green as zmq
import zmq.auth
from zmq.utils.strtypes import asbytes, cast_unicode
from core.workflow import Workflow as wf
from core.case import callbacks
import signal
import core.config.paths
from core.protobuf.build import data_pb2
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

REQUESTS_ADDR = 'tcp://127.0.0.1:5555'
RESULTS_ADDR = 'tcp://127.0.0.1:5556'
COMM_ADDR = 'tcp://127.0.0.1:5557'

logger = logging.getLogger(__name__)


def recreate_workflow(workflow_json):
    """Recreates a workflow from a JSON to prepare for it to be executed.

    Args:
        workflow_json (JSON dict): The input workflow JSON, with some other fields as well.

    Returns:
        (Workflow object, start_input): A tuple containing the reconstructed Workflow object, and the input to
            the start step.
    """
    uid = workflow_json['uid']
    del workflow_json['uid']
    execution_uid = workflow_json['execution_uid']
    del workflow_json['execution_uid']
    start = workflow_json['start']

    start_input = ''
    if 'start_input' in workflow_json:
        start_input = workflow_json['start_input']
        del workflow_json['start_input']

    workflow = wf.from_json(workflow_json)
    workflow.uid = uid
    workflow.execution_uid = execution_uid
    workflow.start = start
    if 'breakpoint_steps' in workflow_json:
        workflow.breakpoint_steps = workflow_json['breakpoint_steps']

    return workflow, start_input


class LoadBalancer:
    def __init__(self, ctx):
        """Initialize a LoadBalancer object, which manages workflow execution.

        Args:
            ctx (Context object): A Context object, shared with the Receiver thread.
        """
        self.available_workers = []
        self.workflow_comms = {}
        self.thread_exit = False
        self.pending_workflows = Queue()

        self.ctx = ctx
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
        """Manages the workflows to be executed and the workers. It waits for the server to submit a request to
        execute a workflow, and then passes the workflow off to an available worker, once one becomes available.
        """
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
        return

    def add_workflow(self, workflow_json):
        """Adds a workflow to the queue to be executed.

        Args:
            workflow_json (dict): Dict representation of a workflow, along with some additional fields necessary for
                reconstructing the workflow.
        """
        self.pending_workflows.put(workflow_json)

    def pause_workflow(self, workflow_execution_uid, workflow_name):
        """Pauses a workflow currently executing.

        Args:
            workflow_execution_uid (str): The execution UID of the workflow.
            workflow_name (str): The name of the workflow.
        """
        logger.info('Pausing workflow {0}'.format(workflow_name))
        if workflow_execution_uid in self.workflow_comms:
            self.comm_socket.send_multipart([self.workflow_comms[workflow_execution_uid], b'', b'Pause'])

    def resume_workflow(self, workflow_execution_uid, workflow_name):
        """Resumes a workflow that has previously been paused.

        Args:
            workflow_execution_uid (str): The execution UID of the workflow.
            workflow_name (str): The name of the workflow.
        """
        logger.info('Resuming workflow {0}'.format(workflow_name))
        if workflow_execution_uid in self.workflow_comms:
            self.comm_socket.send_multipart([self.workflow_comms[workflow_execution_uid], b'', b'resume'])

    def resume_breakpoint_step(self, workflow_execution_uid, workflow_name):
        """Resumes a step in a workflow that was listed as a breakpoint step.

        Args:
            workflow_execution_uid (str): The execution UID of the workflow.
            workflow_name (str): The name of the workflow.
        """
        logger.info('Resuming workflow {0}'.format(workflow_name))
        if workflow_execution_uid in self.workflow_comms:
            self.comm_socket.send_multipart([self.workflow_comms[workflow_execution_uid], b'', b'Resume breakpoint'])

    def send_data_to_trigger(self, data, workflow_uids):
        for uid in workflow_uids:
            if uid in self.workflow_comms:
                self.comm_socket.send_multipart(
                    [self.workflow_comms[uid], b'', str.encode(json.dumps(data))])


class Worker:
    def __init__(self, id_, worker_env=None):
        """Initialize a Workflow object, which will be executing workflows.

        Args:
            id_ (str): The ID of the worker. Needed for ZMQ socket communication.
            worker_env (function, optional): The optional custom function to setup the worker environment. Defaults
                to None.
        """
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGABRT, self.exit_handler)

        def handle_data_sent(sender, **kwargs):
            self.on_data_sent(sender, **kwargs)
        self.handle_data_sent = handle_data_sent
        callbacks.data_sent.connect(handle_data_sent)

        server_secret_file = os.path.join(core.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = zmq.auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(core.config.paths.zmq_private_keys_path, "client.key_secret")
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)

        self.ctx = zmq.Context()

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

        self.results_sock = self.ctx.socket(zmq.PUSH)
        self.results_sock.identity = u"Worker-{}".format(id_).encode("ascii")
        self.results_sock.curve_secretkey = client_secret
        self.results_sock.curve_publickey = client_public
        self.results_sock.curve_serverkey = server_public
        self.results_sock.connect(RESULTS_ADDR)

        if worker_env:
            Worker.setup_worker_env = worker_env

        self.setup_worker_env()
        self.execute_workflow_worker()

    def on_data_sent(self, sender, **kwargs):
        obj_type = kwargs['object_type']
        packet = data_pb2.Message()
        if obj_type == 'Workflow':
            if 'data' in kwargs:
                packet.type = data_pb2.Message.WORKFLOWPACKETDATA
                wf_packet = packet.workflow_packet_data
                wf_packet.additional_data = kwargs['data']
            else:
                packet.type = data_pb2.Message.WORKFLOWPACKET
                wf_packet = packet.workflow_packet
            wf_packet.sender.name = sender.name
            wf_packet.sender.uid = sender.uid
            wf_packet.sender.execution_uid = sender.execution_uid
            wf_packet.callback_name = kwargs['callback_name']
        elif obj_type == 'Step':
            if 'data' in kwargs:
                packet.type = data_pb2.Message.STEPPACKETDATA
                step_packet = packet.step_packet_data
                step_packet.additional_data = kwargs['data']
            else:
                packet.type = data_pb2.Message.STEPPACKET
                step_packet = packet.step_packet
            step_packet.sender.name = sender.name
            step_packet.sender.uid = sender.uid
            step_packet.sender.execution_uid = sender.execution_uid
            step_packet.sender.app = sender.app
            step_packet.sender.action = sender.action

            for key, value in sender.input.items():
                step_packet.sender.input[key] = str(value)

            step_packet.callback_name = kwargs['callback_name']
        elif obj_type in ['NextStep', 'Flag', 'Filter']:
            packet.type = data_pb2.Message.GENERALPACKET
            general_packet = packet.general_packet
            general_packet.sender.uid = sender.uid
            if hasattr(sender, 'app'):
                general_packet.sender.app = sender.app
            general_packet.callback_name = kwargs['callback_name']
        packet_bytes = packet.SerializeToString()
        self.results_sock.send(packet_bytes)

    def exit_handler(self, signum, frame):
        """Clean up upon receiving a SIGINT or SIGABT.
        """
        if self.request_sock:
            self.request_sock.close()
        if self.results_sock:
            self.results_sock.close()
        if self.comm_sock:
            self.comm_sock.close()
        os._exit(0)

    def setup_worker_env(self):
        """Sets up the worker environment, as the Worker executes in a new process.
        """
        import core.config.config
        core.config.config.initialize()

    def execute_workflow_worker(self):
        """Keep executing workflows as they come in over the ZMQ socket from the manager.
        """
        self.request_sock.send(b"Ready")
        self.comm_sock.send(b"Executing")

        while True:
            workflow_in = self.request_sock.recv()

            workflow, start_input = recreate_workflow(json.loads(cast_unicode(workflow_in)))
            workflow.comm_sock = self.comm_sock

            workflow.execute(execution_uid=workflow.execution_uid, start=workflow.start, start_input=start_input)
            self.request_sock.send(b"Done")


class Receiver:
    callback_lookup = {
        'Workflow Execution Start': (callbacks.WorkflowExecutionStart, False),
        'Next Step Found': (callbacks.NextStepFound, False),
        'App Instance Created': (callbacks.AppInstanceCreated, False),
        'Workflow Shutdown': (callbacks.WorkflowShutdown, True),
        'Workflow Input Validated': (callbacks.WorkflowInputInvalid, False),
        'Workflow Input Invalid': (callbacks.WorkflowInputInvalid, False),
        'Workflow Paused': (callbacks.WorkflowPaused, False),
        'Workflow Resumed': (callbacks.WorkflowResumed, False),
        'Step Execution Success': (callbacks.StepExecutionSuccess, True),
        'Step Execution Error': (callbacks.StepExecutionError, True),
        'Step Started': (callbacks.StepStarted, False),
        'Function Execution Success': (callbacks.FunctionExecutionSuccess, True),
        'Step Input Invalid': (callbacks.StepInputInvalid, False),
        'Conditionals Executed': (callbacks.ConditionalsExecuted, False),
        'Next Step Taken': (callbacks.NextStepTaken, False),
        'Next Step Not Taken': (callbacks.NextStepNotTaken, False),
        'Flag Success': (callbacks.FlagSuccess, False),
        'Flag Error': (callbacks.FlagError, False),
        'Filter Success': (callbacks.FilterSuccess, False),
        'Filter Error': (callbacks.FilterError, False)}

    def __init__(self, ctx):
        """Initialize a Receiver object, which will receive callbacks from the execution elements.

        Args:
            ctx (Context object): A Context object, shared with the LoadBalancer thread.
        """
        self.thread_exit = False
        self.workflows_executed = 0

        server_secret_file = os.path.join(core.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = zmq.auth.load_certificate(server_secret_file)

        self.ctx = ctx

        self.results_sock = self.ctx.socket(zmq.PULL)
        self.results_sock.curve_secretkey = server_secret
        self.results_sock.curve_publickey = server_public
        self.results_sock.curve_server = True
        self.results_sock.bind(RESULTS_ADDR)

    @staticmethod
    def send_callback(callback, sender, data):
        """Sends a callback, received from an execution element over a ZMQ socket.

        Args:
            callback (callback object): The callback object to be sent.
            sender (dict): The sender information.
            data (dict): The data associated with the callback.
        """
        if data:
            callback.send(sender, data=data)
        else:
            callback.send(sender)

    def receive_results(self):
        """Keep receiving results from execution elements over a ZMQ socket, and trigger the callbacks.
        """
        while True:
            if self.thread_exit:
                break
            try:
                message_bytes = self.results_sock.recv(zmq.NOBLOCK)
            except zmq.ZMQError:
                gevent.sleep(0.1)
                continue

            message_outer = data_pb2.Message()
            message_outer.ParseFromString(message_bytes)

            if message_outer.type == data_pb2.Message.WORKFLOWPACKET:
                message = message_outer.workflow_packet
            elif message_outer.type == data_pb2.Message.WORKFLOWPACKETDATA:
                message = message_outer.workflow_packet_data
            elif message_outer.type == data_pb2.Message.STEPPACKET:
                message = message_outer.step_packet
            elif message_outer.type == data_pb2.Message.STEPPACKETDATA:
                message = message_outer.step_packet_data
            else:
                message = message_outer.general_packet

            callback_name = message.callback_name
            sender = message.sender
            try:
                callback = self.callback_lookup[callback_name]
                data = json.loads(message.additional_data) if callback[1] else {}
                Receiver.send_callback(callback[0], sender, data)
            except KeyError:
                logger.error('Unknown callback sent {}'.format(callback_name))
            else:
                if callback_name == 'Workflow Shutdown':
                    self.workflows_executed += 1

        self.results_sock.close()
        return
