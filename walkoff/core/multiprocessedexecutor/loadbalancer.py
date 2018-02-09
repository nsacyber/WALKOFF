import json
import logging
import os

import gevent
import zmq.auth as auth
import zmq.green as zmq
from gevent.queue import Queue
from google.protobuf.json_format import MessageToDict
from six import string_types

import walkoff.config.config
import walkoff.config.paths
from walkoff.events import WalkoffEvent
from walkoff.proto.build.data_pb2 import Message, CommunicationPacket, ExecuteWorkflowMessage

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

logger = logging.getLogger(__name__)


class LoadBalancer:
    def __init__(self, ctx):
        """Initialize a LoadBalancer object, which manages workflow execution.

        Args:
            ctx (Context object): A Context object, shared with the Receiver thread.
        """

        self.workers = {}

        self.workflow_comms = {}
        self.thread_exit = False
        self.pending_workflows = Queue()

        @WalkoffEvent.WorkflowShutdown.connect
        def handle_workflow_shutdown(sender, **kwargs):
            self.on_worker_available(sender, **kwargs)

        self.handle_workflow_shutdown = handle_workflow_shutdown

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def handle_workflow_awaiting_data(sender, **kwargs):
            self.on_worker_available(sender, **kwargs)

        self.handle_workflow_awaiting_data = handle_workflow_awaiting_data

        @WalkoffEvent.WorkflowPaused.connect
        def handle_workflow_paused(sender, **kwargs):
            self.on_worker_available(sender, **kwargs)

        self.handle_workflow_paused = handle_workflow_paused

        self.ctx = ctx
        server_secret_file = os.path.join(walkoff.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)

        self.request_socket = self.ctx.socket(zmq.ROUTER)
        self.request_socket.curve_secretkey = server_secret
        self.request_socket.curve_publickey = server_public
        self.request_socket.curve_server = True
        self.request_socket.bind(walkoff.config.config.zmq_requests_address)

        self.comm_socket = self.ctx.socket(zmq.ROUTER)
        self.comm_socket.curve_secretkey = server_secret
        self.comm_socket.curve_publickey = server_public
        self.comm_socket.curve_server = True
        self.comm_socket.bind(walkoff.config.config.zmq_communication_address)

    def manage_workflows(self):
        """Manages the workflows to be executed and the workers. It waits for the server to submit a request to
        execute a workflow, and then passes the workflow off to an available worker, once one becomes available.
        """
        while True:
            if self.thread_exit:
                break

            if len(self.workers) < walkoff.config.config.num_processes:
                try:
                    worker, message = self.request_socket.recv_multipart(flags=zmq.NOBLOCK)
                    if message == b"Ready":
                        self.workers[worker] = walkoff.config.config.num_threads_per_process
                except zmq.ZMQError:
                    pass

            # There is a worker available and a workflow in the queue, so pop it off and send it to the worker
            if any(val > 0 for val in self.workers.values()) and not self.pending_workflows.empty():
                print("Worker available, about to grab workflow")
                workflow_id, workflow_execution_id, start, start_arguments, resume = self.pending_workflows.get()
                print("LB sending workflow to worker")
                worker = self.__get_available_worker()
                self.workflow_comms[workflow_execution_id] = worker

                message = ExecuteWorkflowMessage()
                message.workflow_id = str(workflow_id)
                message.workflow_execution_id = workflow_execution_id
                message.resume = resume

                if start:
                    message.start = str(start)
                if start_arguments:
                    self.__set_arguments_for_proto(message, start_arguments)

                self.request_socket.send_multipart([worker, message.SerializeToString()])

            gevent.sleep(0.1)

        self.request_socket.close()
        self.comm_socket.close()
        return

    def __get_available_worker(self):
        max_avail = 0
        available_worker = None
        for worker, value in self.workers.items():
            if value > max_avail:
                max_avail = value
                available_worker = worker
        if available_worker:
            self.workers[available_worker] -= 1
        return available_worker

    def add_workflow(self, workflow_id, workflow_execution_id, start=None, start_arguments=None, resume=False):
        """Adds a workflow ID to the queue to be executed.

        Args:
            workflow_id (int): The ID of the workflow to be executed.
            workflow_execution_id (str): The execution ID of the workflow to be executed.
            start (str, optional): The ID of the first, or starting action. Defaults to None.
            start_arguments (list[Argument]): The arguments to the starting action of the workflow. Defaults to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.
        """
        print("Workflow placed on queue")
        self.pending_workflows.put((workflow_id, workflow_execution_id, start, start_arguments, resume))

    def pause_workflow(self, workflow_execution_id):
        """Pauses a workflow currently executing.

        Args:
            workflow_execution_id (str): The execution ID of the workflow.
        """
        logger.info('Pausing workflow {0}'.format(workflow_execution_id))
        if workflow_execution_id in self.workflow_comms:
            message = CommunicationPacket()
            message.type = CommunicationPacket.PAUSE
            message.workflow_execution_id = workflow_execution_id
            message_bytes = message.SerializeToString()
            self.comm_socket.send_multipart([self.workflow_comms[workflow_execution_id], message_bytes])
            return True
        else:
            return False

    def resume_workflow(self, workflow_execution_id):
        """Resumes a workflow that has previously been paused.

        Args:
            workflow_execution_id (str): The execution ID of the workflow.
        """
        logger.info('Resuming workflow {0}'.format(workflow_execution_id))
        if workflow_execution_id in self.workflow_comms:
            message = CommunicationPacket()
            message.type = CommunicationPacket.RESUME
            message.workflow_execution_id = workflow_execution_id
            message_bytes = message.SerializeToString()
            self.comm_socket.send_multipart([self.workflow_comms[workflow_execution_id], message_bytes])
            return True
        else:
            return False

    def send_data_to_trigger(self, data_in, workflow_execution_ids, arguments=None):
        """Sends the data_in to the workflows specified in workflow_ids.

        Args:
            data_in (dict): Data to be used to match against the triggers for an Action awaiting data.
            workflow_execution_ids (list[str]): A list of workflow execution IDs to send this data to.
            arguments (list[Argument]): An optional list of Arguments to update for an
                Action awaiting data for a trigger. Defaults to None.
        """
        data = dict()
        data['data_in'] = data_in
        message = CommunicationPacket()
        message.type = CommunicationPacket.TRIGGER
        message.data_in = json.dumps(data)

        if arguments:
            self.__set_arguments_for_proto(message, arguments)

        for execution_id in workflow_execution_ids:
            if execution_id in self.workflow_comms:
                message.workflow_execution_id = execution_id
                message_bytes = message.SerializeToString()
                self.comm_socket.send_multipart([self.workflow_comms[execution_id], message_bytes])

    def send_exit_to_worker_comms(self):
        """Sends the exit message over the communication sockets, otherwise worker receiver threads will hang
        """
        print("Exit called")
        message = CommunicationPacket()
        message.type = CommunicationPacket.EXIT
        message_bytes = message.SerializeToString()
        for worker in self.workers:
            self.comm_socket.send_multipart([worker, message_bytes])

    def on_worker_available(self, sender, **kwargs):
        if sender['workflow_execution_id'] in self.workflow_comms:
            print("Incrementing ")
            print(self.workers)
            worker = self.workflow_comms[sender['workflow_execution_id']]
            self.workers[worker] += 1
            self.workflow_comms.pop(sender['workflow_execution_id'])
            print(self.workers)

    @staticmethod
    def __set_arguments_for_proto(message, arguments):
        for argument in arguments:
            arg = message.arguments.add()
            arg.name = argument.name
            for field in ('value', 'reference', 'selection'):
                val = getattr(argument, field)
                if val is not None:
                    if not isinstance(val, string_types):
                        try:
                            setattr(arg, field, json.dumps(val))
                        except ValueError:
                            setattr(arg, field, str(val))
                    else:
                        setattr(arg, field, val)


class Receiver:
    def __init__(self, ctx):
        """Initialize a Receiver object, which will receive callbacks from the execution elements.

        Args:
            ctx (Context object): A Context object, shared with the LoadBalancer thread.
        """
        self.thread_exit = False
        self.workflows_executed = 0

        server_secret_file = os.path.join(walkoff.config.paths.zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)

        self.ctx = ctx

        self.results_sock = self.ctx.socket(zmq.PULL)
        self.results_sock.curve_secretkey = server_secret
        self.results_sock.curve_publickey = server_public
        self.results_sock.curve_server = True
        self.results_sock.bind(walkoff.config.config.zmq_results_address)

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

            message_outer = Message()

            message_outer.ParseFromString(message_bytes)
            callback_name = message_outer.event_name

            if message_outer.type == Message.WORKFLOWPACKET:
                message = message_outer.workflow_packet
            elif message_outer.type == Message.ACTIONPACKET:
                message = message_outer.action_packet
            elif message_outer.type == Message.USERMESSAGE:
                message = message_outer.message_packet
            else:
                message = message_outer.general_packet

            sender = MessageToDict(message.sender, preserving_proto_field_name=True)

            event = WalkoffEvent.get_event_from_name(callback_name)
            if event is not None:
                if event.requires_data():
                    if event != WalkoffEvent.SendMessage:
                        data = json.loads(message.additional_data)
                    else:
                        data = format_message_event_data(message)
                    event.send(sender, data=data)
                else:
                    event.send(sender)
                if event == WalkoffEvent.WorkflowShutdown:
                    self.workflows_executed += 1
            else:
                logger.error('Unknown callback {} sent'.format(callback_name))

        self.results_sock.close()
        return


def format_message_event_data(message):
    return {'users': message.users,
            'roles': message.roles,
            'requires_reauth': message.requires_reauth,
            'body': json.loads(message.body),
            'subject': message.subject}
