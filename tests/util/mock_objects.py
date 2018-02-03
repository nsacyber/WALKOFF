import json
import threading

import gevent
from google.protobuf.json_format import MessageToDict
from zmq.utils.strtypes import cast_unicode

from walkoff.coredb.argument import Argument
from walkoff.events import WalkoffEvent
from walkoff.core.multiprocessedexecutor import loadbalancer
from walkoff.core.multiprocessedexecutor.worker import convert_to_protobuf
from walkoff.proto.build import data_pb2
import walkoff.coredb.devicedb
from walkoff.coredb.workflow import Workflow

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
        self.manager.pending_workflows.put(("Exit", "Exit"))
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
        self.exec_uid = ''

        def handle_data_sent(sender, **kwargs):
            self.on_data_sent(sender, **kwargs)

        self.handle_data_sent = handle_data_sent
        if not WalkoffEvent.CommonWorkflowSignal.signal.receivers:
            WalkoffEvent.CommonWorkflowSignal.connect(handle_data_sent)

    def on_data_sent(self, sender, **kwargs):
        if self.exec_uid or not hasattr(sender, "_execution_uid"):
            packet_bytes = convert_to_protobuf(sender, self.exec_uid, **kwargs)
        else:
            packet_bytes = convert_to_protobuf(sender, sender.get_execution_uid(), **kwargs)
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

    def add_workflow(self, workflow_id, workflow_execution_uid):
        self.pending_workflows.put((workflow_id, workflow_execution_uid))

    def manage_workflows(self):
        while True:
            workflow_id, workflow_execution_uid = self.pending_workflows.recv()
            if workflow_id == "Exit":
                return

            walkoff.coredb.devicedb.device_db.session.expire_all()
            workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=workflow_id).first()

            self.workflow_comms[workflow_execution_uid] = workflow

            self.exec_uid = workflow_execution_uid

            workflow.execute(execution_uid=workflow_execution_uid, start=workflow.start)
            self.exec_uid = ''

    def pause_workflow(self, workflow_execution_uid):
        if workflow_execution_uid in self.workflow_comms:
            self.workflow_comms[workflow_execution_uid].pause()

    def resume_workflow(self, workflow_execution_uid):
        if workflow_execution_uid in self.workflow_comms:
            self.workflow_comms[workflow_execution_uid].resume()

    def send_data_to_trigger(self, data_in, workflow_uids, arguments=None):
        data = dict()
        data['data_in'] = data_in
        arg_objects = []
        if arguments:
            for arg in arguments:
                arg_objects.append(Argument(**arg))
        data["arguments"] = arg_objects
        for uid in workflow_uids:
            if uid in self.workflow_comms:
                self.workflow_comms[uid].send_data_to_action(data)


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
