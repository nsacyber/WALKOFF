from core.case.callbacks import WorkflowShutdown, WorkflowExecutionStart, StepExecutionError, StepExecutionSuccess
from collections import OrderedDict
from datetime import datetime
import json

max_results = 50

results = OrderedDict()


@WorkflowShutdown.connect
def __workflow_ended_callback(sender, **kwargs):
    global results
    if sender.uid in results:
        results[sender.uid]['completed_at'] = str(datetime.utcnow())
        results[sender.uid]['status'] = 'completed'


@WorkflowExecutionStart.connect
def __workflow_started_callback(sender, **kwargs):
    results[sender.uid] = {'name': sender.name,
                           'started_at': str(datetime.utcnow()),
                           'status': 'running',
                           'results': []}


def __append_step_result(uid, data, step_type):
    global results
    result = {'name': data['name'],
              'result': data['result'],
              'input': data['input'],
              'type': step_type,
              'timestamp': str(datetime.utcnow())}
    results[uid]['results'].append(result)


@StepExecutionSuccess.connect
def __step_execution_success_callback(sender, **kwargs):
    global results
    if sender.uid in results:
        __append_step_result(sender.uid, json.loads(kwargs['data']), 'SUCCESS')


@StepExecutionError.connect
def __step_execution_error_callback(sender, **kwargs):
    global results
    if sender.uid in results:
        __append_step_result(sender.uid, json.loads(kwargs['data']), 'ERROR')