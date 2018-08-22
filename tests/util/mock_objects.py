import json
import threading

import gevent
from fakeredis import FakeStrictRedis
from flask import current_app
from zmq.utils.strtypes import cast_unicode

import walkoff.config
from walkoff.appgateway.appinstancerepo import AppInstanceRepo
from walkoff.cache import RedisCacheAdapter
from walkoff.events import WalkoffEvent
from walkoff.executiondb import ExecutionDatabase
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.multiprocessedexecutor.protoconverter import ProtobufWorkflowResultsConverter as ProtoConverter
from walkoff.multiprocessedexecutor.receiver import Receiver
from walkoff.multiprocessedexecutor.senders import ZMQWorkflowResultsSender
from walkoff.worker.action_exec_strategy import make_execution_strategy
from walkoff.worker.workflow_exec_strategy import WorkflowExecutor

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

workflows_executed = 0


def mock_initialize_threading(self, pids=None):
    global workflows_executed
    workflows_executed = 0

    with current_app.app_context():
        self.zmq_sender = ZMQWorkflowResultsSender(current_app.running_context.execution_db,
                                                   current_app.running_context.case_logger)

    self.manager = MockLoadBalancer(current_app._get_current_object())
    self.manager_thread = threading.Thread(target=self.manager.manage_workflows)
    self.manager_thread.start()

    self.threading_is_initialized = True


def mock_wait_and_reset(self, num_workflows):
    global workflows_executed

    timeout = 0
    shutdown = 10
    while timeout < shutdown:
        if num_workflows == workflows_executed:
            break
        timeout += 0.1
        gevent.sleep(0.1)
    workflows_executed = 0


def mock_shutdown_pool(self):
    if self.manager_thread and self.manager_thread.is_alive():
        self.manager.pending_workflows.put(("Exit", "Exit", "Exit", "Exit", "Exit", "Exit"))
        self.manager_thread.join(timeout=1)
    self.threading_is_initialized = False
    WalkoffEvent.CommonWorkflowSignal.signal.receivers = {}
    self.cleanup_threading()
    return


class MockLoadBalancer(object):
    def __init__(self, current_app):
        self.pending_workflows = MockRequestQueue()
        self.results_queue = MockReceiveQueue(current_app)
        self.workflow_comms = {}

        def handle_data_sent(sender, **kwargs):
            self.on_data_sent(sender, **kwargs)

        self.handle_data_sent = handle_data_sent
        if not WalkoffEvent.CommonWorkflowSignal.signal.receivers:
            WalkoffEvent.CommonWorkflowSignal.connect(handle_data_sent)

        self.execution_db = ExecutionDatabase.instance

        self.workflow_executor = WorkflowExecutor(2, self.execution_db, make_execution_strategy(walkoff.config.Config),
                                                  AppInstanceRepo)

    def on_data_sent(self, sender, **kwargs):
        workflow_ctx = self.workflow_executor.get_current_workflow()
        if kwargs['event'] in [WalkoffEvent.TriggerActionAwaitingData, WalkoffEvent.WorkflowPaused]:
            saved_workflow = SavedWorkflow(workflow_execution_id=workflow_ctx.execution_id,
                                           workflow_id=workflow_ctx.id,
                                           action_id=workflow_ctx.get_executing_action_id(),
                                           app_instances=workflow_ctx.app_instance_repo)
            self.execution_db.session.add(saved_workflow)
            self.execution_db.session.commit()

        packet_bytes = ProtoConverter.event_to_protobuf(sender, workflow_ctx, **kwargs)
        self.results_queue.send(packet_bytes)

    def add_workflow(self, workflow_id, workflow_execution_id, start=None, start_arguments=None, resume=False,
                     environment_variables=None):
        self.pending_workflows.put(
            (workflow_id, workflow_execution_id, start, start_arguments, resume, environment_variables))

    def manage_workflows(self):
        while True:
            workflow_id, workflow_execution_id, start, start_arguments, resume, env_vars = self.pending_workflows.recv()
            if workflow_id == "Exit":
                return

            self.workflow_executor.execute(workflow_id, workflow_execution_id, start, start_arguments, resume, env_vars)

    def pause_workflow(self, workflow_execution_id):
        if workflow_execution_id in self.workflow_comms:
            self.workflow_executor.pause(workflow_execution_id)

    def abort_workflow(self, workflow_execution_id):
        self.workflow_executor.abort(workflow_execution_id)
        return True


class MockReceiveQueue(Receiver):

    def __init__(self, current_app):
        self.current_app = current_app

    def send(self, packet):
        with self.current_app.app_context():
            self._send_callback(packet)

    def _increment_execution_count(self):
        global workflows_executed
        workflows_executed += 1


class MockRequestQueue(object):
    def __init__(self):
        self.queue = Queue()

    def pop(self, flags=None):
        res = self.queue.get()
        return res

    def push(self, data):
        self.queue.put(data)

    def recv(self, flags=None):
        return self.pop(flags)

    def recv_mutipart(self, flags=None):
        return self.pop(flags)

    def put(self, data):
        self.push(data)

    def send(self, data):
        self.push(data)

    def send_json(self, data):
        self.push(data)

    def send_multipart(self, data):
        try:
            workflow_json = json.loads(cast_unicode(data[2]))
            self.push(workflow_json)
        except:
            self.push(data)


class MockRedisCacheAdapter(RedisCacheAdapter):
    def __init__(self, **opts):
        self.cache = FakeStrictRedis(**opts)
        self.cache.info = lambda: None

    def info(self):
        pass


class PubSubCacheSpy(object):
    def __init__(self):
        self.subscribed = []
        self.published = {}

    def subscribe(self, channel):
        self.subscribed.append(channel)

    def publish(self, channel, data):
        if channel not in self.published:
            self.published[channel] = [data]
        else:
            self.published[channel].append(data)

    def shutdown(self):
        pass
