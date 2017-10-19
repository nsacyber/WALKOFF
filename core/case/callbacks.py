import datetime
from six import string_types
import json
from functools import partial
from blinker import Signal
import core.case.subscription as case_subscription
from core.case import database
from core.case.database import Event
from apscheduler.events import (EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                                EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN,
                                EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED)


def __add_entry_to_case_wrapper(sender, data, event_type, entry_message, message_name):
    if isinstance(sender, dict):
        originator = sender['uid']
    else:
        originator = sender.uid
    cases_to_add = case_subscription.get_cases_subscribed(originator, message_name)
    if cases_to_add:
        if not isinstance(data, string_types):
            try:
                data = json.dumps(data)
            except TypeError:
                data = str(data)

        event = Event(type=event_type,
                      timestamp=datetime.datetime.utcnow(),
                      originator=originator,
                      message=entry_message,
                      data=data)
        database.case_db.add_event(event, cases_to_add)


def __construct_logging_signal(event_type, message_name, entry_message):
    """Constructs a blinker Signal to log an event to the log database. Note: The returned callback must be stored to a
        module variable for the signal to work.
        
    Args:
        event_type (str): Type of event which is logged 'Workflow, Step, etc.'
        message_name (str): Name of message
        entry_message (str): More detailed message to log
        
    Returns:
        (signal, callback): The constructed blinker signal and its associated callback.
    """
    signal = Signal(message_name)
    signal_callback = partial(__add_entry_to_case_wrapper,
                              data='',
                              event_type=event_type,
                              entry_message=entry_message,
                              message_name=message_name)
    signal.connect(signal_callback)
    return signal, signal_callback  # need to return a tuple and save it to avoid weak reference


# Controller callbacks
SchedulerStart, __scheduler_start_callback = __construct_logging_signal('System',
                                                                        EVENT_SCHEDULER_START,
                                                                        'Scheduler started')
SchedulerShutdown, __scheduler_shutdown_callback = __construct_logging_signal('System',
                                                                              EVENT_SCHEDULER_SHUTDOWN,
                                                                              'Scheduler shutdown')
SchedulerPaused, __scheduler_paused_callback = __construct_logging_signal('System',
                                                                          EVENT_SCHEDULER_PAUSED,
                                                                          'Scheduler paused')
SchedulerResumed, __scheduler_resumed_callback = __construct_logging_signal('System',
                                                                            EVENT_SCHEDULER_RESUMED,
                                                                            'Scheduler resumed')
SchedulerJobAdded, __scheduler_job_added_callback = __construct_logging_signal('System', EVENT_JOB_ADDED, 'Job Added')
SchedulerJobRemoved, __scheduler_job_removed_callback = __construct_logging_signal('System',
                                                                                   EVENT_JOB_REMOVED,
                                                                                   'Job Removed')
SchedulerJobExecuted, __scheduler_job_executed_callback = __construct_logging_signal('System',
                                                                                     EVENT_JOB_EXECUTED,
                                                                                     'Job executed successfully')
SchedulerJobError, __scheduler_job_error_callback = __construct_logging_signal('System',
                                                                               EVENT_JOB_ERROR,
                                                                               'Job executed with error')

# Workflow callbacks
WorkflowExecutionStart, __workflow_execution_start_callback = __construct_logging_signal('Workflow',
                                                                                         'Workflow Execution Start',
                                                                                         'Workflow execution started')
AppInstanceCreated, __app_instance_created_callback = __construct_logging_signal('Workflow',
                                                                                 'App Instance Created',
                                                                                 'New app instance created')
NextStepFound, __next_step_found_callback = __construct_logging_signal('Workflow', 'Next Step Found', 'Next step found')

WorkflowShutdown, __workflow_shutdown_callback = __construct_logging_signal('Workflow',
                                                                            'Workflow Shutdown',
                                                                            'Workflow shutdown')

WorkflowInputValidated, __workflow_input_validated = __construct_logging_signal('Workflow',
                                                                                'Workflow Input Validated',
                                                                                'Workflow input validated')

WorkflowInputInvalid, __workflow_input_invalidated = __construct_logging_signal('Workflow',
                                                                                'Workflow Input Invalid',
                                                                                'Workflow input invalid')

WorkflowPaused, __workflow_paused = __construct_logging_signal('Workflow',
                                                               'Workflow Paused',
                                                               'Workflow paused')

WorkflowResumed, __workflow_resumed = __construct_logging_signal('Workflow',
                                                                 'Workflow Resumed',
                                                                 'Workflow resumed')

# Step callbacks

FunctionExecutionSuccess, __func_exec_success_callback = __construct_logging_signal('Step',
                                                                                    'Function Execution Success',
                                                                                    'Function executed successfully')
StepExecutionSuccess, __step_execution_success_callback = __construct_logging_signal('Step',
                                                                                     'Step Execution Success',
                                                                                     'Step executed successfully')
StepExecutionError, __step_execution_error_callback = __construct_logging_signal('Step',
                                                                                 'Step Execution Error',
                                                                                 'Step executed with error')
StepStarted, __step_started_callback = __construct_logging_signal('Step',
                                                                  'Step Started',
                                                                  'Step execution started')
StepInputInvalid, __step_input_invalid_callback = __construct_logging_signal('Step',
                                                                             'Input Invalid',
                                                                             'Input is invalid')
ConditionalsExecuted, __conditionals_executed_callback = __construct_logging_signal('Step',
                                                                                    'Conditionals Executed',
                                                                                    'Conditionals executed')

# Next step callbacks
NextStepTaken, __next_step_taken_callback = __construct_logging_signal('Next Step',
                                                                       'Next Step Taken',
                                                                       'Next step taken')
NextStepNotTaken, __next_step_not_taken_callback = __construct_logging_signal('Next Step',
                                                                              'Next Step Not Taken',
                                                                              'Next step not taken')

# Condition callbacks
ConditionSuccess, __condition_success_callback = __construct_logging_signal('Condition',
                                                                  'Condition Success',
                                                                  'Condition executed without error')
ConditionError, __condition_error_callback = __construct_logging_signal('Condition', 'Condition Error', 'Condition executed with error')

# Transform callbacks
TransformSuccess, __transform_success_callback = __construct_logging_signal('Transform', 'Transform Success',
                                                                      'Transform success')
TransformError, __transform_error_callback = __construct_logging_signal('Transform', 'Transform Error', 'Transform error')

# Load Balancer callbacks
data_sent = Signal('sent')
