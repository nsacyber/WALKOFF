import logging
from enum import unique, Enum
from functools import partial

from apscheduler.events import EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, \
    EVENT_SCHEDULER_RESUMED, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from blinker import Signal

from walkoff.case.callbacks import add_entry_to_case

logger = logging.getLogger(__name__)


@unique
class EventType(Enum):
    controller = 1
    playbook = 2
    workflow = 3
    action = 4
    branch = 5
    conditonalexpression = 6
    condition = 7
    transform = 8
    other = 256


class WalkoffSignal(object):
    _signals = {}

    def __init__(self, name, event_type, loggable=True, message=''):
        self.name = name
        self.signal = Signal(name)
        self.event_type = event_type
        self.is_loggable = loggable
        if loggable:
            signal_callback = partial(add_entry_to_case,
                                      data='',
                                      event_type=event_type.name,
                                      entry_message=message,
                                      message_name=name)
            self.connect(signal_callback, weak=False)

    def send(self, sender, **kwargs):
        self.signal.send(sender, **kwargs)

    def connect(self, func, weak=True):
        self.signal.connect(func)
        if not weak:
            WalkoffSignal._store_callback(func)
        return func

    @classmethod
    def _store_callback(cls, func):
        """
        Stores callbacks so they aren't garbage collected and the weak references of the signals disappear
        """
        cls._signals[id(func)] = func


class ControllerSignal(WalkoffSignal):
    def __init__(self, name, message, scheduler_event):
        super(ControllerSignal, self).__init__(name, EventType.controller, message=message)
        self.scheduler_event = scheduler_event


class WorkflowSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(WorkflowSignal, self).__init__(name, EventType.workflow, message=message)


class ActionSignal(WalkoffSignal):
    def __init__(self, name, message, loggable=True):
        super(ActionSignal, self).__init__(name, EventType.action, message=message, loggable=loggable)


class BranchSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(BranchSignal, self).__init__(name, EventType.branch, message=message)


class ConditionalExpressionSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(ConditionalExpressionSignal, self).__init__(name, EventType.conditonalexpression, message=message)


class ConditionSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(ConditionSignal, self).__init__(name, EventType.condition, message=message)


class TransformSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(TransformSignal, self).__init__(name, EventType.transform, message=message)


@unique
class WalkoffEvent(Enum):
    SchedulerStart = ControllerSignal('Scheduler Start', 'Scheduler started', EVENT_SCHEDULER_START)
    SchedulerShutdown = ControllerSignal('Scheduler Shutdown', 'Scheduler shutdown', EVENT_SCHEDULER_SHUTDOWN)
    SchedulerPaused = ControllerSignal('Scheduler Paused', 'Scheduler paused', EVENT_SCHEDULER_PAUSED)
    SchedulerResumed = ControllerSignal('Scheduler Resumed', 'Scheduler resumed', EVENT_SCHEDULER_RESUMED)
    SchedulerJobAdded = ControllerSignal('Job Added', 'Job added', EVENT_JOB_ADDED)
    SchedulerJobRemoved = ControllerSignal('Job Removed', 'Job removed', EVENT_JOB_REMOVED)
    SchedulerJobExecuted = ControllerSignal('Job Executed', 'Job executed successfully', EVENT_JOB_EXECUTED)
    SchedulerJobError = ControllerSignal('Job Error', 'Job executed with error', EVENT_JOB_ERROR)

    WorkflowExecutionStart = WorkflowSignal('Workflow Execution Start', 'Workflow execution started')
    AppInstanceCreated = WorkflowSignal('App Instance Created', 'New app instance created')
    WorkflowShutdown = WorkflowSignal('Workflow Shutdown', 'Workflow shutdown')
    WorkflowArgumentsValidated = WorkflowSignal('Workflow Arguments Validated', 'Workflow arguments validated')
    WorkflowArgumentsInvalid = WorkflowSignal('Workflow Arguments Invalid', 'Workflow arguments invalid')
    WorkflowPaused = WorkflowSignal('Workflow Paused', 'Workflow paused')
    WorkflowResumed = WorkflowSignal('Workflow Resumed', 'Workflow resumed')

    ActionExecutionSuccess = ActionSignal('Action Execution Success', 'Action executed successfully')
    ActionExecutionError = ActionSignal('Action Execution Error', 'Action executed with error')
    ActionStarted = ActionSignal('Action Started', 'Action execution started')
    ActionArgumentsInvalid = ActionSignal('Arguments Invalid', 'Arguments invalid')
    TriggerActionAwaitingData = ActionSignal('Trigger Action Awaiting Data', 'Trigger action awaiting data')
    TriggerActionTaken = ActionSignal('Trigger Action Taken', 'Trigger action taken')
    TriggerActionNotTaken = ActionSignal('Trigger Action Not Taken', 'Trigger action not taken')
    SendMessage = ActionSignal('Message Sent', 'Walkoff message sent', loggable=False)

    BranchTaken = BranchSignal('Branch Taken', 'Branch taken')
    BranchNotTaken = BranchSignal('Branch Not Taken', 'Branch not taken')

    ConditionalExpressionTrue = ConditionalExpressionSignal('Conditional Expression True',
                                                            'Conditional expression evaluated true')
    ConditionalExpressionFalse = ConditionalExpressionSignal('Conditional Expression False',
                                                             'Conditional expression evaluated false')
    ConditionalExpressionError = ConditionalExpressionSignal('Conditional Expression Error',
                                                             'Error occurred while evaluating conditional expression')

    ConditionSuccess = ConditionSignal('Condition Success', 'Condition executed without error')
    ConditionError = ConditionSignal('Condition Error', 'Condition executed with error')

    TransformSuccess = TransformSignal('Transform Success', 'Transform success')
    TransformError = TransformSignal('Transform Error', 'Transform error')

    CommonWorkflowSignal = WalkoffSignal('Common Workflow Signal', EventType.other, loggable=False)

    @property
    def signal_name(self):
        return self.value.name

    @property
    def signal(self):
        return self.value.signal

    @property
    def event_type(self):
        return self.value.event_type

    @classmethod
    def get_event_from_name(cls, event_name):
        return getattr(cls, event_name, None)

    @classmethod
    def get_event_from_signal_name(cls, signal_name):
        return next((event for event in cls if event.signal_name == signal_name), None)

    def requires_data(self):
        return (self in (WalkoffEvent.WorkflowShutdown,
                         WalkoffEvent.ActionExecutionError,
                         WalkoffEvent.ActionExecutionSuccess,
                         WalkoffEvent.SendMessage))

    def send(self, sender, **kwargs):
        self.value.send(sender, **kwargs)

    def connect(self, func, weak=True):
        self.value.connect(func, weak=weak)
        return func

    def is_loggable(self):
        return self.value.is_loggable
