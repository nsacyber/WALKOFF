import threading
import core.controller
from core.case import callbacks
import zmq.green as zmq
import gevent

t = None
running = False


def send_callback(callback, sender, data):
    if 'data' in data:
        callback.send(sender, data=data['data'])
    else:
        callback.send(sender)


def receive(pull_sock):

    while True:

        print("In WRONG receiver loop")

        message = pull_sock.recv_json()

        if 'exit' in message:
            print("Receiver returning")
            return

        callback = message['callback_name']
        sender = message['sender']
        data = message

        print("Receiver got "+callback)

        if callback == "Workflow Execution Start":
            send_callback(callbacks.WorkflowExecutionStart, sender, data)
        elif callback == "Next Step Found":
            send_callback(callbacks.NextStepFound, sender, data)
        elif callback == "App Instance Created":
            send_callback(callbacks.AppInstanceCreated, sender, data)
        elif callback == "Workflow Shutdown":
            send_callback(callbacks.WorkflowShutdown, sender, data)
        elif callback == "Workflow Input Validated":
            send_callback(callbacks.WorkflowInputValidated, sender, data)
        elif callback == "Workflow Input Invalid":
            send_callback(callbacks.WorkflowInputInvalid, sender, data)
        elif callback == "Step Execution Success":
            send_callback(callbacks.StepExecutionSuccess, sender, data)
        elif callback == "Step Execution Error":
            send_callback(callbacks.StepExecutionError, sender, data)
        elif callback == "Step Input Validated":
            send_callback(callbacks.StepInputValidated, sender, data)
        elif callback == "Function Execution Success":
            send_callback(callbacks.FunctionExecutionSuccess, sender, data)
        elif callback == "Step Input Invalid":
            send_callback(callbacks.StepInputInvalid, sender, data)
        elif callback == "Conditionals Executed":
            send_callback(callbacks.ConditionalsExecuted, sender, data)


def start_receiver():
    global t
    global running

    if not running:

        ctx = zmq.Context()
        pull_sock = ctx.socket(zmq.PULL)
        print(core.controller.PUSH_ADDR)
        pull_sock.bind(core.controller.PUSH_ADDR)
        gevent.sleep(2)

        running = True
        t = threading.Thread(target=receive, args=(pull_sock,))
        t.start()


def stop_receiver():
    global t
    global running

    print("Stopping receiver...")

    if running:
        running = False
        t.join()
