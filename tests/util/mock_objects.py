from core import loadbalancer
import json
import threading
import zmq.green as zmq
from zmq.utils.strtypes import cast_unicode
from core.case.callbacks import data_sent
import time

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

workflows_executed = 0


def mock_initialize_threading(self, worker_env=None):
    global workflows_executed
    workflows_executed = 0

    self.load_balancer = MockLoadBalancer()
    self.manager_thread = threading.Thread(target=self.load_balancer.manage_workflows)
    self.manager_thread.start()

    self.threading_is_initialized = True


def mock_shutdown_pool(self, num_workflows=0):
    shutdown = 5
    timed = 0
    while timed < shutdown:
        if (num_workflows == 0) or (num_workflows != 0 and num_workflows == workflows_executed):
            if self.manager_thread and self.manager_thread.is_alive():
                self.load_balancer.pending_workflows.put("Exit")
                self.manager_thread.join()
            self.threading_is_initialized = False
            break
        timed += 0.1
        time.sleep(0.1)
    self.cleanup_threading()
    return


class MockLoadBalancer(object):
    def __init__(self):
        self.pending_workflows = MockRequestQueue()
        self.comm_queue = MockCommQueue()
        self.results_queue = MockReceiveQueue()
        self.workflow_comms = {}

        def handle_data_sent(sender, **kwargs):
            self.on_data_sent(sender, **kwargs)
        self.handle_data_sent = handle_data_sent
        if not data_sent.receivers:
            data_sent.connect(handle_data_sent)

    def on_data_sent(self, sender, **kwargs):
        self.results_queue.send_json(kwargs['data'])

    def add_workflow(self, workflow_json):
        self.pending_workflows.put(workflow_json)

    def manage_workflows(self):
        while True:
            workflow_json = self.pending_workflows.recv()
            if workflow_json == "Exit":
                return

            self.workflow_comms[workflow_json['execution_uid']] = 'worker'

            workflow, start_input = loadbalancer.recreate_workflow(workflow_json)
            workflow.set_comm_sock(self.comm_queue)

            workflow.execute(execution_uid=workflow.execution_uid, start=workflow.start, start_input=start_input)

    def pause_workflow(self, workflow_execution_uid, workflow_name):
        if workflow_execution_uid in self.workflow_comms:
            self.comm_queue.status = b"Pause"

    def resume_workflow(self, workflow_execution_uid, workflow_name):
        if workflow_execution_uid in self.workflow_comms:
            self.comm_queue.status = b"resume"

    def resume_breakpoint_step(self, workflow_execution_uid, workflow_name):
        if workflow_execution_uid in self.workflow_comms:
            self.comm_queue.status = b"Resume breakpoint"


class MockCommQueue(object):
    def __init__(self):
        self.status = b"Running"

    def recv(self, flags=None):
        if flags == zmq.NOBLOCK:
            if self.status == b"Pause":
                return self.status
            else:
                raise zmq.ZMQError
        else:
            while self.status != b"resume" and self.status != b"Resume breakpoint":
                pass
            return self.status

    def send(self, data):
        pass


class MockReceiveQueue(loadbalancer.Receiver):
    def __init__(self):
        pass

    def send_json(self, data):
        global workflows_executed

        callback_name = data['callback_name']
        sender = data['sender']

        callback = self.callback_lookup[callback_name]
        data = data if callback[1] else {}
        loadbalancer.Receiver.send_callback(callback[0], sender, data)

        if callback_name == 'Workflow Shutdown':
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
