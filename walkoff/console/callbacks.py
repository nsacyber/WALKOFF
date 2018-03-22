from gevent.event import Event, AsyncResult
from gevent import sleep
from walkoff.helpers import create_sse_event
import threading

console_event_json = AsyncResult()
console_signal = Event()
console_event_id_counter = 0

def console_event_stream():
    global console_event_id_counter
    print("STARTED")
    console_signal.wait()
    print("SET!")
    while True:
        event_type, data = console_event_json.get()
        yield create_sse_event(event_id=console_event_id_counter, event=event_type, data=data)
        console_event_id_counter += 1
        console_signal.wait()

def format_console_data(sender, data):
    result = {}
    result["message"] = data
    return result

# def send_console_result_to_sse(result, event):
#     console_event_json.set((event, result))
#     sleep(0)
#     print(console_signal)
#     console_signal.set()
#     console_signal.clear()
#     sleep(0)

def console_log_callback(sender, data):
    data = format_console_data(sender, data)
    console_event_json.set(("log", data))
    console_signal.set()
    console_signal.clear()
    # send_console_result_to_sse(data, "log")