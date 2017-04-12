import datetime
import logging
import uuid
from functools import partial
from blinker import Signal
import core.case.subscription as case_subscription
from core.case import database

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, \
    EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED

logging.basicConfig()  # needed so apscheduler can log to console when an error occurs


class _EventEntry(object):
    """
    Container for event entries

    Attributes:
        uuid (str): a unique identifier
        timestamp (str): time of creation
        type (str): type of event logged
        caller (str): name/id of the object which created the event
        ancestry (list[str]): callchain which produced the event
        message (str): Event message
        data: other information attached to event
    """

    def __init__(self, sender, entry_type, entry_message, data=None, name=""):
        self.uuid = str(uuid.uuid4())
        self.timestamp = datetime.datetime.utcnow()
        self.type = entry_type
        self.caller = (sender.name if hasattr(sender, "name") else sender.id) if not name else name
        self.ancestry = list(sender.ancestry)
        self.message = entry_message
        self.data = data

    def __repr__(self):
        return str({
            "uuid": self.uuid,
            "timestamp": self.timestamp,
            "type": str(self.type),
            "caller": str(self.caller),
            "ancestry": str(self.ancestry),
            "message": str(self.message),
            "data": str(self.data)
        })


def __add_entry_to_case_db(sender, event, message_name):
    cases_to_add = [case for case in case_subscription.subscriptions
                    if case_subscription.is_case_subscribed(case, sender.ancestry, message_name)]
    if cases_to_add:
        database.case_db.add_event(event, cases_to_add)


def __add_entry_to_case_wrapper(sender, data, event_type, message_name, entry_message):
    __add_entry_to_case_db(sender, _EventEntry(sender, event_type, entry_message, data), message_name)


def __construct_logging_signal(event_type, message_name, entry_message):
    """
    Constructs a blinker Signal to log an event to the log database. Note: The returned callback must be stored to a
    module variable for the signal to work.
    :param event_type (str): Type of event whcih is logged 'Workflow, Step, etc.'
    :param message_name (str): Name of message
    :param entry_message (str): More detailed message to log
    :param data (str): Extra information
    :return: (signal, callback): The constructed blinker signal and its associated callback.
    """
    signal = Signal(message_name)
    signal_callback = partial(__add_entry_to_case_wrapper,
                              data='',
                              event_type=event_type,
                              message_name=message_name,
                              entry_message=entry_message)
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
AppInstanceCreated, __app_instance_created_callback = __construct_logging_signal('Workflow',
                                                                                 'InstanceCreated',
                                                                                 'New app instance created')
StepExecutionSuccess, __step_execution_success_callback = __construct_logging_signal('Workflow',
                                                                                     'StepExecutionSuccess',
                                                                                     'Step executed successfully')
NextStepFound, __next_step_found_callback = __construct_logging_signal('Workflow', 'NextStepFound', 'Next step found')

WorkflowShutdown, __workflow_shutdown_callback = __construct_logging_signal('Workflow',
                                                                            'WorkflowShutdown',
                                                                            'Workflow shutdown')

# Step callbacks

FunctionExecutionSuccess, __func_exec_success_callback = __construct_logging_signal('Step',
                                                                                    'FunctionExecutionSuccess',
                                                                                    'Function executed successfully')

StepInputValidated, __step_input_validated_callback = __construct_logging_signal('Step',
                                                                                 'InputValidated',
                                                                                 'Input successfully validated')
ConditionalsExecuted, __conditionals_executed_callback = __construct_logging_signal('Step',
                                                                                    'ConditionalsExecuted',
                                                                                    'Conditionals executed')

# Next step callbacks
NextStepTaken, __next_step_taken_callback = __construct_logging_signal('Next Step', 'NextStepTaken', 'Next step taken')
NextStepNotTaken, __next_step_not_taken_callback = __construct_logging_signal('Next Step',
                                                                              'NextStepNotTaken',
                                                                              'Next step not taken')

# Flag callbacks
FlagArgsValid, __flag_args_valid_callback = __construct_logging_signal('Flag', 'FlagArgsValid', 'Flag arguments valid')
FlagArgsInvalid, __flag_args_invalid_callback = __construct_logging_signal('Flag',
                                                                           'FlagArgsInvalid',
                                                                           'Flag arguments invalid')

# Filter callbacks
FilterSuccess, __filter_success_callback = __construct_logging_signal('Filter', 'FilterSuccess', 'Filter success')
FilterError, __filter_error_callback = __construct_logging_signal('Filter', 'FilterError', 'Filter error')
