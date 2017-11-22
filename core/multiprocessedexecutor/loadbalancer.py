import json
import logging
import os

import gevent
import zmq.auth as auth
import zmq.green as zmq
from gevent.queue import Queue
from zmq.utils.strtypes import asbytes

from core.argument import Argument
import core.config.config
import core.config.paths
from core.protobuf.build import data_pb2
from google.protobuf.json_format import MessageToDict

try:
    from Queue import Queue
except ImportError:
    from queue import Queue
from core.case import callbacks

REQUESTS_ADDR = 'tcp://127.0.0.1:5555'
RESULTS_ADDR = 'tcp://127.0.0.1:5556'
COMM_ADDR = 'tcp://127.0.0.1:5557'

logger = logging.getLogger(__name__)


class LoadBalancer:
    def __init__(self, ctx):
        """Initialize a LoadBalancer object, which manages workflow execution.

        Args:
            ctx (Context object): A Context object, shared with the Receiver thread.
        """
        self.available_workers = []
        self.registered_workers = []
        self.workflow_comms = {}
        self.thread_exit = False
        self.pending_workflows = Queue()

        self.ctx = ctx
        server_secret_file = os.path.join(core.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)

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
                    if ready == b"Done":
                        self.available_workers.append(worker)
                        self.workflow_comms = {uid: worker for uid, proc in self.workflow_comms.items() if proc != worker}
                    elif ready == b"Ready":
                        self.registered_workers.append(worker)
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

    def pause_workflow(self, workflow_execution_uid):
        """Pauses a workflow currently executing.

        Args:
            workflow_execution_uid (str): The execution UID of the workflow.
        """
        logger.info('Pausing workflow {0}'.format(workflow_execution_uid))
        if workflow_execution_uid in self.workflow_comms:
            self.comm_socket.send_multipart([self.workflow_comms[workflow_execution_uid], b'', b'Pause'])

    def resume_workflow(self, workflow_execution_uid):
        """Resumes a workflow that has previously been paused.

        Args:
            workflow_execution_uid (str): The execution UID of the workflow.
        """
        logger.info('Resuming workflow {0}'.format(workflow_execution_uid))
        if workflow_execution_uid in self.workflow_comms:
            self.comm_socket.send_multipart([self.workflow_comms[workflow_execution_uid], b'', b'Resume'])

    def send_data_to_trigger(self, data_in, workflow_uids, arguments=None):
        """Sends the data_in to the workflows specified in workflow_uids.

        Args:
            data_in (dict): Data to be used to match against the triggers for an Action awaiting data.
            workflow_uids (list[str]): A list of workflow execution UIDs to send this data to.
            arguments (list[Argument]): An optional list of Arguments to update for a Action awaiting data for a trigger.
                Defaults to None.
        """
        data = dict()
        data['data_in'] = data_in
        data['arguments'] = arguments if arguments else []
        for uid in workflow_uids:
            if uid in self.workflow_comms:
                self.comm_socket.send_multipart(
                    [self.workflow_comms[uid], b'', str.encode(json.dumps(data))])

    def send_exit_to_worker_comms(self):
        """Sends the exit message over the communication sockets, otherwise worker receiver threads will hang
        """
        for worker in self.registered_workers:
            self.comm_socket.send_multipart([worker, b'', b'Exit'])


class Receiver:
    callback_lookup = {
        'Workflow Execution Start': (callbacks.WorkflowExecutionStart, False),
        'App Instance Created': (callbacks.AppInstanceCreated, False),
        'Workflow Shutdown': (callbacks.WorkflowShutdown, True),
        'Workflow Arguments Validated': (callbacks.WorkflowArgumentsValidated, False),
        'Workflow Arguments Invalid': (callbacks.WorkflowArgumentsInvalid, False),
        'Workflow Paused': (callbacks.WorkflowPaused, False),
        'Workflow Resumed': (callbacks.WorkflowResumed, False),
        'Action Execution Error': (callbacks.ActionExecutionError, True),
        'Action Started': (callbacks.ActionStarted, False),
        'Action Execution Success': (callbacks.ActionExecutionSuccess, True),
        'Action Argument Invalid': (callbacks.ActionArgumentsInvalid, False),
        'Branch Taken': (callbacks.BranchTaken, False),
        'Branch Not Taken': (callbacks.BranchNotTaken, False),
        'Condition Success': (callbacks.ConditionSuccess, False),
        'Condition Error': (callbacks.ConditionError, False),
        'Transform Success': (callbacks.TransformSuccess, False),
        'Transform Error': (callbacks.TransformError, False),
        'Trigger Action Taken': (callbacks.TriggerActionTaken, False),
        'Trigger Action Not Taken': (callbacks.TriggerActionNotTaken, False),
        'Trigger Action Awaiting Data': (callbacks.TriggerActionAwaitingData, False)
    }

    def __init__(self, ctx):
        """Initialize a Receiver object, which will receive callbacks from the execution elements.

        Args:
            ctx (Context object): A Context object, shared with the LoadBalancer thread.
        """
        self.thread_exit = False
        self.workflows_executed = 0

        server_secret_file = os.path.join(core.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)

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
            elif message_outer.type == data_pb2.Message.ACTIONPACKET:
                message = message_outer.action_packet
            elif message_outer.type == data_pb2.Message.ACTIONPACKETDATA:
                message = message_outer.action_packet_data
            else:
                message = message_outer.general_packet

            callback_name = message.callback_name
            sender = MessageToDict(message.sender, preserving_proto_field_name=True)

            try:
                callback = self.callback_lookup[callback_name]
                data = json.loads(message.additional_data) if callback[1] else {}
                Receiver.send_callback(callback[0], sender, data)
            except KeyError:
                logger.error('Unknown callback {} sent'.format(callback_name))
            else:
                if callback_name == 'Workflow Shutdown':
                    self.workflows_executed += 1

        self.results_sock.close()
        return
