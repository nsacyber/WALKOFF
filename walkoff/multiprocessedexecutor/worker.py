import json
import logging
import os
import signal
import threading
import time

import nacl.bindings
import nacl.utils
import zmq
import zmq.auth as auth
from concurrent.futures import ThreadPoolExecutor
from google.protobuf.json_format import MessageToDict
from nacl.public import PrivateKey, Box
from six import string_types

import walkoff.cache
import walkoff.config
import walkoff.executiondb
from walkoff import initialize_databases
from walkoff.appgateway.appinstancerepo import AppInstanceRepo
from walkoff.events import EventType, WalkoffEvent
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb.workflow import Workflow
from walkoff.proto.build.data_pb2 import Message, CommunicationPacket, ExecuteWorkflowMessage, CaseControl, WorkflowControl
import walkoff.cache
import walkoff.case.database as casedb
from walkoff.case.logger import CaseLogger
from walkoff.case.subscription import Subscription, SubscriptionCache
from threading import Lock

logger = logging.getLogger(__name__)


def convert_to_protobuf(sender, workflow, **kwargs):
    """Converts an execution element and its data to a protobuf message.

    Args:
        sender (execution element): The execution element object that is sending the data.
        workflow (Workflow): The workflow which is sending the event
        kwargs (dict, optional): A dict of extra fields, such as data, callback_name, etc.

    Returns:
        The newly formed protobuf object, serialized as a string to send over the ZMQ socket.
    """
    event = kwargs['event']
    data = kwargs['data'] if 'data' in kwargs else None
    packet = Message()
    packet.event_name = event.name
    if event.event_type == EventType.workflow:
        convert_workflow_to_proto(packet, workflow, data)
    elif event.event_type == EventType.action:
        if event == WalkoffEvent.SendMessage:
            convert_send_message_to_protobuf(packet, sender, workflow, **kwargs)
        else:
            convert_action_to_proto(packet, sender, workflow, data)
    elif event.event_type in (
            EventType.branch, EventType.condition, EventType.transform, EventType.conditonalexpression):
        convert_branch_transform_condition_to_proto(packet, sender, workflow)
    packet_bytes = packet.SerializeToString()
    return packet_bytes


def convert_workflow_to_proto(packet, sender, data=None):
    packet.type = Message.WORKFLOWPACKET
    workflow_packet = packet.workflow_packet
    if 'data' is not None:
        workflow_packet.additional_data = json.dumps(data)
    add_workflow_to_proto(workflow_packet.sender, sender)


def convert_send_message_to_protobuf(packet, message, workflow, **kwargs):
    packet.type = Message.USERMESSAGE
    message_packet = packet.message_packet
    message_packet.subject = message.pop('subject', '')
    message_packet.body = json.dumps(message['body'])
    add_workflow_to_proto(message_packet.workflow, workflow)
    if 'users' in kwargs:
        message_packet.users.extend(kwargs['users'])
    if 'roles' in kwargs:
        message_packet.roles.extend(kwargs['roles'])
    if 'requires_reauth' in kwargs:
        message_packet.requires_reauth = kwargs['requires_reauth']


def convert_action_to_proto(packet, sender, workflow, data=None):
    packet.type = Message.ACTIONPACKET
    action_packet = packet.action_packet
    if 'data' is not None:
        action_packet.additional_data = json.dumps(data)
    add_sender_to_action_packet_proto(action_packet, sender)
    add_arguments_to_action_proto(action_packet, sender)
    add_workflow_to_proto(action_packet.workflow, workflow)


def add_sender_to_action_packet_proto(action_packet, sender):
    action_packet.sender.name = sender.name
    action_packet.sender.id = str(sender.id)
    action_packet.sender.execution_id = sender.get_execution_id()
    action_packet.sender.app_name = sender.app_name
    action_packet.sender.action_name = sender.action_name
    action_packet.sender.device_id = sender.device_id if sender.device_id is not None else -1


def add_arguments_to_action_proto(action_packet, sender):
    for argument in sender.arguments:
        arg = action_packet.sender.arguments.add()
        arg.name = argument.name
        for field in ('value', 'reference', 'selection'):
            val = getattr(argument, field)
            if val is not None:
                if not isinstance(val, string_types):
                    try:
                        setattr(arg, field, json.dumps(val))
                    except (ValueError, TypeError):
                        setattr(arg, field, str(val))
                else:
                    setattr(arg, field, val)


def add_workflow_to_proto(packet, workflow):
    packet.name = workflow.name
    packet.id = str(workflow.id)
    packet.execution_id = str(workflow.get_execution_id())


def convert_branch_transform_condition_to_proto(packet, sender, workflow):
    packet.type = Message.GENERALPACKET
    general_packet = packet.general_packet
    general_packet.sender.id = str(sender.id)
    add_workflow_to_proto(general_packet.workflow, workflow)
    if hasattr(sender, 'app_name'):
        general_packet.sender.app_name = sender.app_name


class Worker(object):
    def __init__(self, id_, num_threads_per_process, zmq_private_keys_path, zmq_results_address,
                 zmq_communication_address, worker_environment_setup=None):
        """Initialize a Workflow object, which will be executing workflows.

        Args:
            id_ (str): The ID of the worker. Needed for ZMQ socket communication.
            worker_environment_setup (func, optional): Function to setup globals in the worker.
        """

        self.id_ = id_
        self._lock = Lock()
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGABRT, self.exit_handler)

        @WalkoffEvent.CommonWorkflowSignal.connect
        def handle_data_sent(sender, **kwargs):
            self.on_data_sent(sender, **kwargs)

        self.handle_data_sent = handle_data_sent

        self.thread_exit = False

        server_secret_file = os.path.join(zmq_private_keys_path, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(zmq_private_keys_path, "client.key_secret")
        client_public, client_secret = auth.load_certificate(client_secret_file)

        ctx = zmq.Context()

        self.comm_sock = ctx.socket(zmq.SUB)
        self.comm_sock.identity = u"Worker-{}".format(id_).encode("ascii")
        self.comm_sock.curve_secretkey = client_secret
        self.comm_sock.curve_publickey = client_public
        self.comm_sock.curve_serverkey = server_public
        self.comm_sock.setsockopt(zmq.SUBSCRIBE, '')
        self.comm_sock.connect(zmq_communication_address)

        self.results_sock = ctx.socket(zmq.PUSH)
        self.results_sock.identity = u"Worker-{}".format(id_).encode("ascii")
        self.results_sock.curve_secretkey = client_secret
        self.results_sock.curve_publickey = client_public
        self.results_sock.curve_serverkey = server_public
        self.results_sock.connect(zmq_results_address)

        self.key = PrivateKey(client_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES])
        self.server_key = PrivateKey(server_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES]).public_key

        if worker_environment_setup:
            worker_environment_setup()
        else:
            walkoff.config.initialize()
            initialize_databases()

        from walkoff.config import Config
        self.cache = walkoff.cache.make_cache(Config.CACHE)

        self.capacity = num_threads_per_process
        self.subscription_cache = SubscriptionCache()
        self.case_logger = CaseLogger(casedb.case_db, self.subscription_cache)

        self.comm_thread = threading.Thread(target=self.receive_data)
        self.comm_thread.start()

        self.workflows = {}
        self.threadpool = ThreadPoolExecutor(max_workers=self.capacity)

        self.receive_requests()

    def exit_handler(self, signum, frame):
        """Clean up upon receiving a SIGINT or SIGABT.
        """
        self.thread_exit = True
        if self.threadpool:
            self.threadpool.shutdown()
        if self.comm_thread:
            self.comm_thread.join(timeout=2)
        for socket in (self.results_sock, self.comm_sock):
            if socket:
                socket.close()
        walkoff.executiondb.execution_db.tear_down()
        os._exit(0)

    def receive_requests(self):
        """Receives requests to execute workflows, and sends them off to worker threads"""
        while True:

            if not self.__is_pool_at_capacity:
                received_message = self.cache.rpop("request_queue")
                if received_message is not None:
                    box = Box(self.key, self.server_key)
                    dec_msg = box.decrypt(received_message)

                    message = ExecuteWorkflowMessage()
                    message.ParseFromString(dec_msg)
                    start = message.start if hasattr(message, 'start') else None

                    start_arguments = []
                    if hasattr(message, 'arguments'):
                        for arg in message.arguments:
                            start_arguments.append(Argument(**(MessageToDict(arg, preserving_proto_field_name=True))))

                    self.threadpool.submit(self.execute_workflow_worker, message.workflow_id,
                                           message.workflow_execution_id, start, start_arguments, message.resume)
            time.sleep(0.1)

    @property
    def __is_pool_at_capacity(self):
        with self._lock:
            return len(self.workflows) >= self.capacity

    def execute_workflow_worker(self, workflow_id, workflow_execution_id, start, start_arguments=None, resume=False):
        """Execute a workflow.
        """
        walkoff.executiondb.execution_db.session.expire_all()
        workflow = walkoff.executiondb.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()
        workflow._execution_id = workflow_execution_id
        if resume:
            saved_state = walkoff.executiondb.execution_db.session.query(SavedWorkflow).filter_by(
                workflow_execution_id=workflow_execution_id).first()
            workflow._accumulator = saved_state.accumulator
            workflow._instance_repo = AppInstanceRepo(saved_state.app_instances)

        with self._lock:
            self.workflows[threading.current_thread().name] = workflow

        start = start if start else workflow.start
        workflow.execute(execution_id=workflow_execution_id, start=start, start_arguments=start_arguments,
                         resume=resume)
        with self._lock:
            self.workflows.pop(threading.current_thread().name)

    def receive_data(self):
        """Constantly receives data from the ZMQ socket and handles it accordingly.
        """

        while True:
            if self.thread_exit:
                break
            try:
                message_bytes = self.comm_sock.recv()
            except zmq.ZMQError:
                continue

            message = CommunicationPacket()
            message.ParseFromString(message_bytes)
            message_type = message.type
            if message_type == CommunicationPacket.WORKFLOW:
                self._handle_workflow_control_packet(message.workflow_control_message)
            elif message_type == CommunicationPacket.CASE:
                self._handle_case_control_packet(message.case_control_message)
            elif message_type == CommunicationPacket.EXIT:
                break

    def _handle_workflow_control_packet(self, message):
        workflow = self.__get_workflow_by_execution_id(message.workflow_execution_id)
        if workflow:
            if message.type == WorkflowControl.PAUSE:
                workflow.pause()
            elif message.type == WorkflowControl.ABORT:
                workflow.abort()

    def _handle_case_control_packet(self, message):
        if message.type == CaseControl.CREATE:
            self.subscription_cache.add_subscriptions(
                message.id,
                [Subscription(sub.id, sub.events) for sub in message.subscriptions])
        elif message.type == CaseControl.UPDATE:
            self.subscription_cache.update_subscriptions(
                message.id,
                [Subscription(sub.id, sub.events) for sub in message.subscriptions])
        elif message.type == CaseControl.DELETE:
            self.subscription_cache.delete_case(message.id)

    def on_data_sent(self, sender, **kwargs):
        """Listens for the data_sent callback, which signifies that an execution element needs to trigger a
                callback in the main thread.

            Args:
                sender (execution element): The execution element that sent the signal.
                kwargs (dict): Any extra data to send.
        """
        workflow = self._get_current_workflow()
        event = kwargs['event']
        if event in [WalkoffEvent.TriggerActionAwaitingData, WalkoffEvent.WorkflowPaused]:
            saved_workflow = SavedWorkflow(
                workflow_execution_id=workflow.get_execution_id(),
                workflow_id=workflow.id,
                action_id=workflow.get_executing_action_id(),
                accumulator=workflow.get_accumulator(),
                app_instances=workflow.get_instances())
            walkoff.executiondb.execution_db.session.add(saved_workflow)
            walkoff.executiondb.execution_db.session.commit()

        packet_bytes = convert_to_protobuf(sender, workflow, **kwargs)
        self.case_logger.log(event, sender.id, kwargs.get('data', None))
        self.results_sock.send(packet_bytes)

    def _get_current_workflow(self):
        with self._lock:
            return self.workflows[threading.currentThread().name]

    def __get_workflow_by_execution_id(self, workflow_execution_id):
        with self._lock:
            for workflow in self.workflows.values():
                if workflow.get_execution_id() == workflow_execution_id:
                    return workflow
            return None
