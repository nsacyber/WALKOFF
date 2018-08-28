import logging
import os
import signal
import threading
import time
from threading import Lock

import nacl.bindings
import nacl.utils
from concurrent.futures import ThreadPoolExecutor
from nacl.public import PrivateKey

import walkoff.cache
import walkoff.config
from walkoff.appgateway.appinstancerepo import AppInstanceRepo
from walkoff.events import WalkoffEvent
from walkoff.executiondb import ExecutionDatabase
from walkoff.worker.action_exec_strategy import make_execution_strategy
from walkoff.worker.zmq_workflow_receivers import WorkerCommunicationMessageType, WorkflowCommunicationMessageType, \
    WorkflowReceiver
from walkoff.worker.workflow_exec_strategy import WorkflowExecutor
from walkoff.senders_receivers_helpers import make_results_sender, make_communication_receiver

logger = logging.getLogger(__name__)


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
            walkoff.config.Config.load_env_vars()

        self.cache = walkoff.cache.make_cache(walkoff.config.Config.CACHE)

        self.execution_db = ExecutionDatabase(walkoff.config.Config.EXECUTION_DB_TYPE,
                                              walkoff.config.Config.EXECUTION_DB_PATH)

        @WalkoffEvent.CommonWorkflowSignal.connect
        def handle_data_sent(sender, **kwargs):
            self.on_data_sent(sender, **kwargs)

        self.handle_data_sent = handle_data_sent

        self.thread_exit = False

        socket_id = u"Worker-{}".format(id_).encode("ascii")

        key = PrivateKey(walkoff.config.Config.CLIENT_PRIVATE_KEY[:nacl.bindings.crypto_box_SECRETKEYBYTES])
        server_key = PrivateKey(
            walkoff.config.Config.SERVER_PRIVATE_KEY[:nacl.bindings.crypto_box_SECRETKEYBYTES]).public_key

        self.capacity = walkoff.config.Config.NUMBER_THREADS_PER_PROCESS

        self.workflow_receiver = WorkflowReceiver(key, server_key, walkoff.config.Config.CACHE)
        data = {'execution_db': self.execution_db, 'socket_id': socket_id}
        self.workflow_results_sender = make_results_sender(**data)
        data = {'socket_id': socket_id}
        self.workflow_communication_receiver = make_communication_receiver(**data)

        action_execution_strategy = make_execution_strategy(walkoff.config.Config)

        self.workflow_executor = WorkflowExecutor(self.capacity, self.execution_db, action_execution_strategy,
                                                  AppInstanceRepo)

        self.comm_thread = threading.Thread(target=self.receive_communications)
        self.comm_thread.start()

        self.workflows = {}
        self.threadpool = ThreadPoolExecutor(max_workers=self.capacity)

        self.wait_for_ready()

        self.receive_workflows()

    def wait_for_ready(self):
        while True:
            if self.workflow_receiver.is_ready() and self.workflow_results_sender.is_ready() and \
                    self.workflow_communication_receiver.is_ready():
                break

        self.workflow_results_sender.send_ready_message()

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
            if not self.workflow_executor.is_at_capacity:
                workflow_data = next(workflow_generator)
                if workflow_data is not None:
                    self.threadpool.submit(self.workflow_executor.execute, *workflow_data)
            time.sleep(0.1)

    def receive_communications(self):
        """Constantly receives data from the ZMQ socket and handles it accordingly"""
        for message in self.workflow_communication_receiver.receive_communications():
            if message.type == WorkerCommunicationMessageType.workflow:
                self._handle_workflow_control_communication(message.data)

    def _handle_workflow_control_communication(self, message):
        if message.type == WorkflowCommunicationMessageType.pause:
            self.workflow_executor.pause(message.workflow_execution_id)
        elif message.type == WorkflowCommunicationMessageType.abort:
            self.workflow_executor.abort(message.workflow_execution_id)

    def on_data_sent(self, sender, **kwargs):
        """Listens for the data_sent callback, which signifies that an execution element needs to trigger a
                callback in the main thread.

            Args:
                sender (ExecutionElement): The execution element that sent the signal.
                kwargs (dict): Any extra data to send.
        """
        workflow_context = self.workflow_executor.get_current_workflow()
        if workflow_context is None and kwargs['event'] != WalkoffEvent.WorkerReady:
            logger.error('Workflow context information does not exist for callback being sent.')
        else:
            self.workflow_results_sender.handle_event(workflow_context, sender, **kwargs)
