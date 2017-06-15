from core.case.callbacks import WorkflowShutdown
from collections import deque
from datetime import datetime
import json

max_results = 50

results = deque(maxlen=max_results)


def reset_max_results(max_len):
    global results
    new_results = deque(maxlen=max_len)
    while results:
        new_results.append(results.popleft())
    results = new_results


def __workflow_ended_callback(sender, **kwargs):
    data = 'None'
    if 'data' in kwargs:
        data = kwargs['data']
    results.append({'name': sender.name,
                    'timestamp': str(datetime.utcnow()),
                    'result': data})


WorkflowShutdown.connect(__workflow_ended_callback)
