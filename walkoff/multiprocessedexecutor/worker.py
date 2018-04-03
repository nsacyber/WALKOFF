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

import walkoff.config
from walkoff.executiondb import ExecutionDatabase
from walkoff.case.database import CaseDatabase
from walkoff.appgateway.appinstancerepo import AppInstanceRepo
from walkoff.events import WalkoffEvent
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb.workflow import Workflow
from walkoff.proto.build.data_pb2 import CommunicationPacket, ExecuteWorkflowMessage, CaseControl, \
    WorkflowControl
import walkoff.cache
from walkoff.case.logger import CaseLogger
from walkoff.case.subscription import Subscription, SubscriptionCache
from threading import Lock
from walkoff.multiprocessedexecutor.proto_helpers import convert_to_protobuf

logger = logging.getLogger(__name__)


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
        self.comm_sock.setsockopt(zmq.SUBSCRIBE, b'')
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
            self.execution_db = ExecutionDatabase(walkoff.config.Config.EXECUTION_DB_TYPE,
                                                  walkoff.config.Config.EXECUTION_DB_PATH)
            self.case_db = CaseDatabase(walkoff.config.Config.CASE_DB_TYPE, walkoff.config.Config.CASE_DB_PATH)

        from walkoff.config import Config
        self.cache = walkoff.cache.make_cache(Config.CACHE)

        self.capacity = num_threads_per_process
        self.subscription_cache = SubscriptionCache()
        self.case_logger = CaseLogger(self.case_db, self.subscription_cache)

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
        self.execution_db.tear_down()
        self.cache.shutdown()
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
        self.execution_db.session.expire_all()
        workflow = self.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()
        workflow._execution_id = workflow_execution_id
        if resume:
            saved_state = self.execution_db.session.query(SavedWorkflow).filter_by(
                workflow_execution_id=workflow_execution_id).first()
            workflow._accumulator = saved_state.accumulator

            for branch in workflow.branches:
                if branch.id in workflow._accumulator:
                    branch._counter = workflow._accumulator[branch.id]

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
            self.execution_db.session.add(saved_workflow)
            self.execution_db.session.commit()
        elif kwargs['event'] == WalkoffEvent.ConsoleLog:
            action = workflow.get_executing_action()
            sender = action

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
