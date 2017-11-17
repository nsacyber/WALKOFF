from enum import unique, Enum
from functools import partial

from apscheduler.events import EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, \
    EVENT_SCHEDULER_RESUMED, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from blinker import Signal

from core.case.callbacks import _add_entry_to_case_wrapper


@unique
class EventType(Enum):
    controller = 1
    playbook = 2
    workflow = 3
    action = 4
    branch = 5
    condition = 6
    transform = 7
    other = 256


class WalkoffSignal(object):
    signals = {}

    def __init__(self, name, event_type, loggable=True, message=''):
        self.name = name
        self.signal = Signal(name)
        self.event_type = event_type
        if loggable:
            signal_callback = partial(_add_entry_to_case_wrapper,
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

    @classmethod
    def _store_callback(cls, func):
        """
        Stores callbacks so they aren't garabage collected and the weakrefs of the signals disappear
        """
        cls.signals[id(func)] = func


class ControllerSignal(WalkoffSignal):
    name_event_conversion = {
        'Scheduler Start': EVENT_SCHEDULER_START,
        'Scheduler Shutdown': EVENT_SCHEDULER_SHUTDOWN,
        'Scheduler Paused': EVENT_SCHEDULER_PAUSED,
        'Scheduler Resumed': EVENT_SCHEDULER_RESUMED,
        'Job Added': EVENT_JOB_ADDED,
        'Job Removed': EVENT_JOB_REMOVED,
        'Job Executed': EVENT_JOB_EXECUTED,
        'Job Error': EVENT_JOB_ERROR}

    def __init__(self, name, message):
        super(ControllerSignal, self).__init__(name, EventType.controller, message=message)
        self.scheduler_event = self.name_event_conversion.get(name, 0)


class WorkflowSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(WorkflowSignal, self).__init__(name, EventType.workflow, message=message)


class ActionSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(ActionSignal, self).__init__(name, EventType.action, message=message)


class BranchSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(BranchSignal, self).__init__(name, EventType.branch, message=message)


class ConditionSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(ConditionSignal, self).__init__(name, EventType.condition, message=message)


class TransformSignal(WalkoffSignal):
    def __init__(self, name, message):
        super(TransformSignal, self).__init__(name, EventType.transform, message=message)


@unique
class WalkoffEvent(Enum):
    SchedulerStart = ControllerSignal('Scheduler Start', 'Scheduler started')
    SchedulerShutdown = ControllerSignal('Scheduler Shutdown', 'Scheduler shutdown')
    SchedulerPaused = ControllerSignal('Scheduler Paused', 'Scheduler paused')
    SchedulerResumed = ControllerSignal('Scheduler Resumed', 'Scheduler resumed')
    SchedulerJobAdded = ControllerSignal('Job Added', 'Job added')
    SchedulerJobRemoved = ControllerSignal('Job Removed', 'Job removed')
    SchedulerJobExecuted = ControllerSignal('Job Executed', 'Job executed successfully')
    SchedulerJobError = ControllerSignal('Job Error', 'Job executed with error')

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

    BranchTaken = BranchSignal('Branch Taken', 'Branch taken')
    BranchNotTaken = BranchSignal('Branch Not Taken', 'Branch not taken')

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
    def send_from_event_name(cls, event_name, sender, **kwargs):
        event = getattr(cls, event_name, None)
        if event is not None:
            event.value.send(sender, **kwargs)
            # TODO: Log otherwise

    @classmethod
    def get_event_from_name(cls, event_name):
        return getattr(cls, event_name, None)

    @classmethod
    def get_event_from_signal_name(cls, signal_name):
        return next((event for event in cls if event.signal_name == signal_name), None)

    def requires_data(self):
        return (self in (WalkoffEvent.WorkflowShutdown,
                         WalkoffEvent.ActionExecutionError,
                         WalkoffEvent.ActionExecutionSuccess))

    def send(self, sender, **kwargs):
        self.value.send(sender, **kwargs)

    def connect(self, func, weak=True):
        self.value.connect(func, weak=weak)
