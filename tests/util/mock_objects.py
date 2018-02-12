import json
import threading

import gevent
from google.protobuf.json_format import MessageToDict
from zmq.utils.strtypes import cast_unicode

from walkoff.events import WalkoffEvent
from walkoff.core.multiprocessedexecutor import loadbalancer
from walkoff.core.multiprocessedexecutor.worker import convert_to_protobuf
from walkoff.proto.build import data_pb2
import walkoff.coredb.devicedb
from walkoff.coredb.workflow import Workflow
from walkoff.coredb.saved_workflow import SavedWorkflow

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

workflows_executed = 0


def mock_initialize_threading(self, pids):
    global workflows_executed
    workflows_executed = 0

    self.manager = MockLoadBalancer()
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
        self.manager.pending_workflows.put(("Exit", "Exit", "Exit", "Exit", "Exit"))
        self.manager_thread.join(timeout=1)
    self.threading_is_initialized = False
    WalkoffEvent.CommonWorkflowSignal.signal.receivers = {}
    self.cleanup_threading()
    return


class MockLoadBalancer(object):
    def __init__(self):
        self.pending_workflows = MockRequestQueue()
        self.results_queue = MockReceiveQueue()
        self.workflow_comms = {}
        self.exec_id = ''

        def handle_data_sent(sender, **kwargs):
            self.on_data_sent(sender, **kwargs)

        self.handle_data_sent = handle_data_sent
        if not WalkoffEvent.CommonWorkflowSignal.signal.receivers:
            WalkoffEvent.CommonWorkflowSignal.connect(handle_data_sent)

    def on_data_sent(self, sender, **kwargs):

        if kwargs['event'] in [WalkoffEvent.TriggerActionAwaitingData, WalkoffEvent.WorkflowPaused]:
            workflow = self.workflow_comms[sender._execution_id]
            saved_workflow = SavedWorkflow(workflow_execution_id=workflow.get_execution_id(),
                                           workflow_id=workflow.id,
                                           action_id=workflow.get_executing_action_id(),
                                           accumulator=workflow.get_accumulator(),
                                           app_instances=workflow.get_instances())
            walkoff.coredb.devicedb.device_db.session.add(saved_workflow)
            walkoff.coredb.devicedb.device_db.session.commit()

        if self.exec_id or not hasattr(sender, "_execution_id"):
            packet_bytes = convert_to_protobuf(sender, self.exec_id, **kwargs)
        else:
            packet_bytes = convert_to_protobuf(sender, sender.get_execution_id(), **kwargs)
        message_outer = data_pb2.Message()
        message_outer.ParseFromString(packet_bytes)

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

        sender = message.sender
        self.results_queue.send(sender, kwargs)

    def add_workflow(self, workflow_id, workflow_execution_id, start=None, start_arguments=None, resume=False):
        self.pending_workflows.put((workflow_id, workflow_execution_id, start, start_arguments, resume))

    def manage_workflows(self):
        while True:
            workflow_id, workflow_execution_id, start, start_arguments, resume = self.pending_workflows.recv()
            if workflow_id == "Exit":
                return

            walkoff.coredb.devicedb.device_db.session.expire_all()
            workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=workflow_id).first()

            self.workflow_comms[workflow_execution_id] = workflow

            self.exec_id = workflow_execution_id

            start = start if start else workflow.start
            workflow.execute(execution_id=workflow_execution_id, start=start, start_arguments=start_arguments, resume=resume)
            self.exec_id = ''

    def pause_workflow(self, workflow_execution_id):
        if workflow_execution_id in self.workflow_comms:
            self.workflow_comms[workflow_execution_id].pause()


class MockReceiveQueue(loadbalancer.Receiver):
    def __init__(self):
        pass

    def send(self, sender, kwargs):
        global workflows_executed

        event = kwargs['event']

        sender = MessageToDict(sender, preserving_proto_field_name=True)
        if event is not None:
            if event.requires_data():
                event.send(sender, data=kwargs['data'])
            else:
                event.send(sender)
            if event == WalkoffEvent.WorkflowShutdown:
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
