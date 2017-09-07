from core import loadbalancer
from core import workflow as wf
import json
import threading
import zmq.green as zmq
from zmq.utils.strtypes import cast_unicode
try:
    from Queue import Queue
except ImportError:
    from queue import Queue


def mock_initialize_threading(self, worker_env=None):
    self.requests_queue = MockSocket(Queue())
    self.comm_queue = MockSocket(Queue())
    self.results_queue = MockSocket(Queue())

    self.receiver = MockReceiver(self.results_queue)
    self.receiver_thread = threading.Thread(target=self.receiver.receive_results)
    self.receiver_thread.start()

    self.load_balancer = MockLoadBalancer(self.requests_queue, self.comm_queue, self.results_queue)
    self.manager_thread = threading.Thread(target=self.load_balancer.manage_workflows)
    self.manager_thread.start()

    self.threading_is_initialized = True


def mock_shutdown_pool(self, num_workflows=0):
    while True:
        if (num_workflows == 0) or \
                (num_workflows != 0 and self.receiver is not None and num_workflows == self.receiver.workflows_executed):
            if self.manager_thread:
                self.requests_queue.put("Exit")
                self.manager_thread.join()
            if self.receiver_thread:
                self.results_queue.put("Exit")
                self.receiver_thread.join()
            self.threading_is_initialized = False
            break
    self.cleanup_threading()
    return


class MockLoadBalancer(object):
    def __init__(self, requests_queue, comm_queue, results_queue):
        self.requests_queue = requests_queue
        self.pending_workflows = requests_queue
        self.comm_queue = comm_queue
        self.comm_socket = self.comm_queue
        self.results_queue = results_queue
        self.workflow_comms = {}

    def manage_workflows(self):
        while True:
            workflow_json = self.requests_queue.recv()

            if workflow_json == "Exit":
                return

            self.workflow_comms[workflow_json['execution_uid']] = 'worker'

            uid = workflow_json['uid']
            del workflow_json['uid']
            execution_uid = workflow_json['execution_uid']
            del workflow_json['execution_uid']
            start = workflow_json['start']

            start_input = ''
            if 'start_input' in workflow_json:
                start_input = workflow_json['start_input']
                del workflow_json['start_input']

            workflow = wf.Workflow()
            workflow.from_json(workflow_json)
            workflow.uid = uid
            workflow.execution_uid = execution_uid
            workflow.start = start
            workflow.results_sock = self.results_queue
            workflow.comm_sock = self.comm_queue
            if 'breakpoint_steps' in workflow_json:
                workflow.breakpoint_steps = workflow_json['breakpoint_steps']

            workflow.execute(execution_uid=execution_uid, start=start, start_input=start_input)


class MockSocket(object):
    def __init__(self, queue):
        self.queue = queue

    def pop(self, flags=None):
        if flags == zmq.NOBLOCK:
            if not self.queue.empty():
                try:
                    res = self.queue.get_nowait()
                except:
                    raise zmq.ZMQError
                else:
                    print("Socket popping {} off queue ZMQ".format(res))
                    return res
            else:
                raise zmq.ZMQError
        else:
            res = self.queue.get()
            print("Socket popping {} off queue".format(res))
            return res

    def push(self, data):
        print("Socket putting {} on queue".format(data))
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


class MockReceiver(loadbalancer.Receiver):
    def __init__(self, results_queue):
        self.workflows_executed = 0
        self.results_queue = results_queue

    def receive_results(self):
        while True:
            message = self.results_queue.recv()

            if message == "Exit":
                print("Receiver exiting")
                return

            callback_name = message['callback_name']
            sender = message['sender']
            data = message

            callback = self.callback_lookup[callback_name]
            data = data if callback[1] else {}
            print("Receiver got {}".format(callback_name))
            print(message)
            import sys
            sys.stdout.flush()
            loadbalancer.Receiver.send_callback(callback[0], sender, data)

            if callback_name == 'Workflow Shutdown':
                self.workflows_executed += 1
