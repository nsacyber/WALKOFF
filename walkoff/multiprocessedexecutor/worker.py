import logging
import os
import signal
import threading
import time
from collections import namedtuple
from threading import Lock

import nacl.bindings
import nacl.utils
import zmq
import zmq.auth as auth
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import DecodeError
from nacl.exceptions import CryptoError
from nacl.public import PrivateKey, Box
from zmq.error import ZMQError

import walkoff.cache
import walkoff.config
from walkoff.appgateway.appinstancerepo import AppInstanceRepo
from walkoff.case.database import CaseDatabase
from walkoff.case.logger import CaseLogger
from walkoff.case.subscription import Subscription, SubscriptionCache
from walkoff.events import WalkoffEvent
from walkoff.executiondb import ExecutionDatabase
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.environment_variable import EnvironmentVariable
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb.workflow import Workflow
from walkoff.multiprocessedexecutor.proto_helpers import convert_to_protobuf
from walkoff.proto.build.data_pb2 import CommunicationPacket, ExecuteWorkflowMessage, CaseControl, \
    WorkflowControl
from walkoff.executiondb.workflowresults import WorkflowStatus, WorkflowStatusEnum

logger = logging.getLogger(__name__)


class WorkflowResultsHandler(object):
    def __init__(self, socket_id, client_secret_key, client_public_key, server_public_key, zmq_results_address,
                 execution_db, case_logger):
        """Initialize a WorkflowResultsHandler object, which will be sending results of workflow execution

        Args:
            socket_id (str): The ID for the results socket
            client_secret_key (str): The secret key for the client
            client_public_key (str): The public key for the client
            server_public_key (str): The public key for the server
            zmq_results_address (str): The address for the ZMQ results socket
            execution_db (ExecutionDatabase): An ExecutionDatabase connection object
            case_logger (CaseLoger): A CaseLogger instance
        """
        self.results_sock = zmq.Context().socket(zmq.PUSH)
        self.results_sock.identity = socket_id
        self.results_sock.curve_secretkey = client_secret_key
        self.results_sock.curve_publickey = client_public_key
        self.results_sock.curve_serverkey = server_public_key
        try:
            self.results_sock.connect(zmq_results_address)
        except ZMQError:
            logger.exception('Workflow Results handler could not connect to {}!'.format(zmq_results_address))
            raise

        self.execution_db = execution_db

        self.case_logger = case_logger

    def shutdown(self):
        """Shuts down the results socket and tears down the ExecutionDatabase
        """
        self.results_sock.close()
        self.execution_db.tear_down()

    def handle_event(self, workflow, sender, **kwargs):
        """Listens for the data_sent callback, which signifies that an execution element needs to trigger a
                callback in the main thread.

            Args:
                workflow (Workflow): The Workflow object that triggered the event
                sender (ExecutionElement): The execution element that sent the signal.
                kwargs (dict): Any extra data to send.
        """
        event = kwargs['event']
        if event in [WalkoffEvent.TriggerActionAwaitingData, WalkoffEvent.WorkflowPaused]:
            saved_workflow = SavedWorkflow.from_workflow(workflow)
            self.execution_db.session.add(saved_workflow)
            self.execution_db.session.commit()
        elif kwargs['event'] == WalkoffEvent.ConsoleLog:
            action = workflow.get_executing_action()
            sender = action

        packet_bytes = convert_to_protobuf(sender, workflow, **kwargs)
        if event.is_loggable():
            self.case_logger.log(event, sender.id, kwargs.get('data', None))
        self.results_sock.send(packet_bytes)


class WorkerCommunicationMessageType(Enum):
    workflow = 1
    case = 2
    exit = 3


class WorkflowCommunicationMessageType(Enum):
    pause = 1
    abort = 2


class CaseCommunicationMessageType(Enum):
    create = 1
    update = 2
    delete = 3


WorkerCommunicationMessageData = namedtuple('WorkerCommunicationMessageData', ['type', 'data'])

WorkflowCommunicationMessageData = namedtuple('WorkflowCommunicationMessageData', ['type', 'workflow_execution_id'])

CaseCommunicationMessageData = namedtuple('CaseCommunicationMessageData', ['type', 'case_id', 'subscriptions'])


class WorkflowCommunicationReceiver(object):
    def __init__(self, socket_id, client_secret_key, client_public_key, server_public_key, zmq_communication_address):
        """Initialize a WorkflowCommunicationReceiver object, which will receive messages on the comm socket

        Args:
            socket_id (str): The socket ID for the ZMQ communication socket
            client_secret_key (str): The secret key for the client
            client_public_key (str): The public key for the client
            server_public_key (str): The public key for the server
            zmq_communication_address (str): The IP address for the ZMQ communication socket
        """
        self.comm_sock = zmq.Context().socket(zmq.SUB)
        self.comm_sock.identity = socket_id
        self.comm_sock.curve_secretkey = client_secret_key
        self.comm_sock.curve_publickey = client_public_key
        self.comm_sock.curve_serverkey = server_public_key
        self.comm_sock.setsockopt(zmq.SUBSCRIBE, b'')
        try:
            self.comm_sock.connect(zmq_communication_address)
        except ZMQError:
            logger.exception('Workflow Communication Receiver could not connect to {}!'.format(
                zmq_communication_address))
            raise
        self.exit = False

    def shutdown(self):
        """Shuts down the object by setting self.exit to True and closing the communication socket
        """
        logger.debug('Shutting down Workflow Communication Recevier')
        self.exit = True
        self.comm_sock.close()

    def receive_communications(self):
        """Constantly receives data from the ZMQ socket and handles it accordingly"""
        logger.info('Starting workflow communication receiver')
        while not self.exit:
            try:
                message_bytes = self.comm_sock.recv()
            except zmq.ZMQError:
                continue

            message = CommunicationPacket()
            try:
                message.ParseFromString(message_bytes)
            except DecodeError:
                logger.error('Worker communication handler could not decode communication packet')
            else:
                message_type = message.type
                if message_type == CommunicationPacket.WORKFLOW:
                    logger.debug('Worker received workflow communication packet')
                    yield WorkerCommunicationMessageData(
                        WorkerCommunicationMessageType.workflow,
                        self._format_workflow_message_data(message.workflow_control_message))
                elif message_type == CommunicationPacket.CASE:
                    logger.debug('Workflow received case communication packet')
                    yield WorkerCommunicationMessageData(
                        WorkerCommunicationMessageType.case,
                        self._format_case_message_data(message.case_control_message))
                elif message_type == CommunicationPacket.EXIT:
                    logger.info('Worker received exit message')
                    break
        raise StopIteration

    @staticmethod
    def _format_workflow_message_data(message):
        workflow_execution_id = message.workflow_execution_id
        if message.type == WorkflowControl.PAUSE:
            return WorkflowCommunicationMessageData(WorkflowCommunicationMessageType.pause, workflow_execution_id)
        elif message.type == WorkflowControl.ABORT:
            return WorkflowCommunicationMessageData(WorkflowCommunicationMessageType.abort, workflow_execution_id)

    @staticmethod
    def _format_case_message_data(message):
        if message.type == CaseControl.CREATE:
            return CaseCommunicationMessageData(
                CaseCommunicationMessageType.create,
                message.id,
                [Subscription(sub.id, sub.events) for sub in message.subscriptions])
        elif message.type == CaseControl.UPDATE:
            return CaseCommunicationMessageData(
                CaseCommunicationMessageType.update,
                message.id,
                [Subscription(sub.id, sub.events) for sub in message.subscriptions])
        elif message.type == CaseControl.DELETE:
            return CaseCommunicationMessageData(CaseCommunicationMessageType.delete, message.id, None)


class WorkflowReceiver(object):
    def __init__(self, key, server_key, cache_config):
        """Initializes a WorkflowReceiver object, which receives workflow execution requests and ships them off to a
            worker to execute

        Args:
            key (PrivateKey): The NaCl PrivateKey generated by the Worker
            server_key (PrivateKey): The NaCl PrivateKey generated by the Worker
            cache_config (dict): Cache configuration
        """
        self.key = key
        self.server_key = server_key
        self.cache = walkoff.cache.make_cache(cache_config)
        self.exit = False

    def shutdown(self):
        """Shuts down the object by setting self.exit to True and shutting down the cache
        """
        logger.debug('Shutting down Workflow Receiver')
        self.exit = True
        self.cache.shutdown()

    def receive_workflows(self):
        """Receives requests to execute workflows, and sends them off to worker threads"""
        logger.info('Starting workflow receiver')
        box = Box(self.key, self.server_key)
        while not self.exit:
            received_message = self.cache.rpop("request_queue")
            if received_message is not None:
                try:
                    decrypted_msg = box.decrypt(received_message)
                except CryptoError:
                    logger.error('Worker could not decrypt received workflow message')
                    continue
                try:
                    message = ExecuteWorkflowMessage()
                    message.ParseFromString(decrypted_msg)
                except DecodeError:
                    logger.error('Workflow could not decode received workflow message')
                else:
                    start = message.start if hasattr(message, 'start') else None

                    start_arguments = []
                    if hasattr(message, 'arguments'):
                        for arg in message.arguments:
                            start_arguments.append(
                                Argument(**(MessageToDict(arg, preserving_proto_field_name=True))))

                    env_vars = []
                    if hasattr(message, 'environment_variables'):
                        for env_var in message.environment_variables:
                            env_vars.append(
                                EnvironmentVariable(**(MessageToDict(env_var, preserving_proto_field_name=True))))

                    yield message.workflow_id, message.workflow_execution_id, start, \
                          start_arguments, message.resume, env_vars
            else:
                yield None
        raise StopIteration


class Worker(object):
    def __init__(self, id_, config_path):
        """Initialize a Workfer object, which will be managing the execution of Workflows

        Args:
            id_ (str): The ID of the worker
            config_path (str): The path to the configuration file to be loaded
        """
        logger.info('Spawning worker {}'.format(id_))
        self.id_ = id_
        self._lock = Lock()
        signal.signal(signal.SIGINT, self.exit_handler)
        signal.signal(signal.SIGABRT, self.exit_handler)

        if os.name == 'nt':
            walkoff.config.initialize(config_path=config_path)
        else:
            walkoff.config.Config.load_config(config_path)

        self.execution_db = ExecutionDatabase(walkoff.config.Config.EXECUTION_DB_TYPE,
                                              walkoff.config.Config.EXECUTION_DB_PATH)
        self.case_db = CaseDatabase(walkoff.config.Config.CASE_DB_TYPE, walkoff.config.Config.CASE_DB_PATH)

        @WalkoffEvent.CommonWorkflowSignal.connect
        def handle_data_sent(sender, **kwargs):
            self.on_data_sent(sender, **kwargs)

        self.handle_data_sent = handle_data_sent

        self.thread_exit = False

        server_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "client.key_secret")
        client_public, client_secret = auth.load_certificate(client_secret_file)

        socket_id = u"Worker-{}".format(id_).encode("ascii")

        key = PrivateKey(client_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES])
        server_key = PrivateKey(server_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES]).public_key

        self.cache = walkoff.cache.make_cache(walkoff.config.Config.CACHE)

        self.capacity = walkoff.config.Config.NUMBER_THREADS_PER_PROCESS
        self.subscription_cache = SubscriptionCache()

        case_logger = CaseLogger(self.case_db, self.subscription_cache)

        self.workflow_receiver = WorkflowReceiver(key, server_key, walkoff.config.Config.CACHE)

        self.workflow_results_sender = WorkflowResultsHandler(
            socket_id,
            client_secret,
            client_public,
            server_public,
            walkoff.config.Config.ZMQ_RESULTS_ADDRESS,
            self.execution_db,
            case_logger)

        self.workflow_communication_receiver = WorkflowCommunicationReceiver(
            socket_id,
            client_secret,
            client_public,
            server_public,
            walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS)

        self.comm_thread = threading.Thread(target=self.receive_communications)

        self.comm_thread.start()

        self.workflows = {}
        self.threadpool = ThreadPoolExecutor(max_workers=self.capacity)

        self.receive_workflows()

    def exit_handler(self, signum, frame):
        """Clean up upon receiving a SIGINT or SIGABT"""
        logger.info('Worker received exit signal {}'.format(signum))
        self.thread_exit = True
        self.workflow_receiver.shutdown()
        if self.threadpool:
            self.threadpool.shutdown()
        self.workflow_communication_receiver.shutdown()
        if self.comm_thread:
            self.comm_thread.join(timeout=2)
        self.workflow_results_sender.shutdown()
        os._exit(0)

    def receive_workflows(self):
        """Receives requests to execute workflows, and sends them off to worker threads"""
        workflow_generator = self.workflow_receiver.receive_workflows()
        while not self.thread_exit:
            if not self.__is_pool_at_capacity:
                workflow_data = next(workflow_generator)
                if workflow_data is not None:
                    self.threadpool.submit(self.execute_workflow_worker, *workflow_data)
            time.sleep(0.1)

    @property
    def __is_pool_at_capacity(self):
        with self._lock:
            return len(self.workflows) >= self.capacity

    def execute_workflow_worker(self, workflow_id, workflow_execution_id, start, start_arguments=None, resume=False,
                                environment_variables=None):
        """Execute a workflow

        Args:
            workflow_id (UUID): The ID of the Workflow to be executed
            workflow_execution_id (UUID): The execution ID of the Workflow to be executed
            start (UUID): The ID of the starting Action
            start_arguments (list[Argument], optional): Optional list of starting Arguments. Defaults to None
            resume (bool, optional): Optional boolean to signify that this Workflow is being resumed. Defaults to False.
            environment_variables (list[EnvironmentVariable]): Optional list of environment variables to pass into
                the workflow. These will not be persistent.
        """
        self.execution_db.session.expire_all()

        workflow_status = self.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=workflow_execution_id).first()
        if workflow_status.status == WorkflowStatusEnum.aborted:
            return

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
                         resume=resume, environment_variables=environment_variables)
        with self._lock:
            self.workflows.pop(threading.current_thread().name)

    def receive_communications(self):
        """Constantly receives data from the ZMQ socket and handles it accordingly"""
        for message in self.workflow_communication_receiver.receive_communications():
            if message.type == WorkerCommunicationMessageType.workflow:
                self._handle_workflow_control_communication(message.data)
            elif message.type == WorkerCommunicationMessageType.case:
                self._handle_case_control_communication(message.data)

    def _handle_workflow_control_communication(self, message):
        workflow = self.__get_workflow_by_execution_id(message.workflow_execution_id)
        if workflow:
            if message.type == WorkflowCommunicationMessageType.pause:
                workflow.pause()
            elif message.type == WorkflowCommunicationMessageType.abort:
                workflow.abort()

    def _handle_case_control_communication(self, message):
        if message.type == CaseCommunicationMessageType.create:
            self.subscription_cache.add_subscriptions(message.case_id, message.subscriptions)
        elif message.type == CaseCommunicationMessageType.update:
            self.subscription_cache.update_subscriptions(message.case_id, message.subscriptions)
        elif message.type == CaseCommunicationMessageType.delete:
            self.subscription_cache.delete_case(message.case_id)

    def on_data_sent(self, sender, **kwargs):
        """Listens for the data_sent callback, which signifies that an execution element needs to trigger a
                callback in the main thread.

            Args:
                sender (ExecutionElement): The execution element that sent the signal.
                kwargs (dict): Any extra data to send.
        """
        workflow = self._get_current_workflow()
        self.workflow_results_sender.handle_event(workflow, sender, **kwargs)

    def _get_current_workflow(self):
        with self._lock:
            return self.workflows[threading.currentThread().name]

    def __get_workflow_by_execution_id(self, workflow_execution_id):
        with self._lock:
            for workflow in self.workflows.values():
                if workflow.get_execution_id() == workflow_execution_id:
                    return workflow
            return None
