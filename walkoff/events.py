import logging
from functools import partial

from apscheduler.events import (EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED,
    EVENT_SCHEDULER_RESUMED, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR)
from blinker import Signal
from enum import unique, Enum

from walkoff.case.callbacks import add_entry_to_case

logger = logging.getLogger(__name__)


@unique
class EventType(Enum):
    """The types of Walkoff events
    """
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
    """A signal to send Walkoff data

    The class is a wrapper around a blinker.Signal

    Attributes:
        name (str): The name of the signal
        signal (Signal): The signal object which sends the event and data
        event_type (EventType): The event type of this signal
        is_loggable (bool): Should this event get logged into cases?
        message (str): The message log with this signal to a case

    Args:
        name (str): The name of the signal
        event_type (EventType): The event type of this signal
        loggable (bool, optional): Should this event get logged into cases? Defaults to True
        message (str, optional): The message log with this signal to a case. Defaults to empty string
    """
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
        """Sends the signal with data

        Args:
            sender: The thing that is sending the signal

        Kwargs:
            data: Additional data to send with the signal
        """
        self.signal.send(sender, **kwargs)

    def connect(self, func, weak=True):
        """A decorator which registers a function as a callback for this signal

        Args:
            func (func): The function to register
            weak (bool, optional): Should a weak reference be used for this connection? Defaults to True

        Returns:
            func: The function connected
        """
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
    """A signal used by controller events

    Attributes:
        scheduler_event (int): The APScheduler event connected to this signal

    Args:
        name (str): The name of the signal
        message (str): The message log with this signal to a case. Defaults to empty string
        scheduler_event (int): The APScheduler event connected to this signal.
    """
    def __init__(self, name, message, scheduler_event):
        super(ControllerSignal, self).__init__(name, EventType.controller, message=message)
        self.scheduler_event = scheduler_event


class WorkflowSignal(WalkoffSignal):
    """A signal used by workflow events

    Args:
        name (str): The name of the signal
        message (str): The message log with this signal to a case. Defaults to empty string
    """
    def __init__(self, name, message):
        super(WorkflowSignal, self).__init__(name, EventType.workflow, message=message)


class ActionSignal(WalkoffSignal):
    """A signal used by action events

    Args:
        name (str): The name of the signal
        message (str): The message log with this signal to a case. Defaults to empty string
        loggable (bool, optional): Should this event get logged into cases? Defaults to True
    """
    def __init__(self, name, message, loggable=True):
        super(ActionSignal, self).__init__(name, EventType.action, message=message, loggable=loggable)


class BranchSignal(WalkoffSignal):
    """A signal used by branch events

        Args:
            name (str): The name of the signal
            message (str): The message log with this signal to a case. Defaults to empty string
    """
    def __init__(self, name, message):
        super(BranchSignal, self).__init__(name, EventType.branch, message=message)


class ConditionalExpressionSignal(WalkoffSignal):
    """A signal used by conditional expression events

        Args:
            name (str): The name of the signal
            message (str): The message log with this signal to a case. Defaults to empty string
    """
    def __init__(self, name, message):
        super(ConditionalExpressionSignal, self).__init__(name, EventType.conditonalexpression, message=message)


class ConditionSignal(WalkoffSignal):
    """A signal used by conditional events

        Args:
            name (str): The name of the signal
            message (str): The message log with this signal to a case. Defaults to empty string
    """
    def __init__(self, name, message):
        super(ConditionSignal, self).__init__(name, EventType.condition, message=message)


class TransformSignal(WalkoffSignal):
    """A signal used by transform events

        Args:
            name (str): The name of the signal
            message (str): The message log with this signal to a case. Defaults to empty string
    """
    def __init__(self, name, message):
        super(TransformSignal, self).__init__(name, EventType.transform, message=message)


@unique
class WalkoffEvent(Enum):
    """The types of events used by Walkoff. The value of the Enum is a signal which can be used to send and event
    """
    SchedulerStart = ControllerSignal('Scheduler Start', 'Scheduler started', EVENT_SCHEDULER_START)
    SchedulerShutdown = ControllerSignal('Scheduler Shutdown', 'Scheduler shutdown', EVENT_SCHEDULER_SHUTDOWN)
    SchedulerPaused = ControllerSignal('Scheduler Paused', 'Scheduler paused', EVENT_SCHEDULER_PAUSED)
    SchedulerResumed = ControllerSignal('Scheduler Resumed', 'Scheduler resumed', EVENT_SCHEDULER_RESUMED)
    SchedulerJobAdded = ControllerSignal('Job Added', 'Job added', EVENT_JOB_ADDED)
    SchedulerJobRemoved = ControllerSignal('Job Removed', 'Job removed', EVENT_JOB_REMOVED)
    SchedulerJobExecuted = ControllerSignal('Job Executed', 'Job executed successfully', EVENT_JOB_EXECUTED)
    SchedulerJobError = ControllerSignal('Job Error', 'Job executed with error', EVENT_JOB_ERROR)

    WorkflowExecutionPending = WorkflowSignal('Workflow Execution Pending', 'Workflow execution pending')
    WorkflowExecutionStart = WorkflowSignal('Workflow Execution Start', 'Workflow execution started')
    AppInstanceCreated = WorkflowSignal('App Instance Created', 'New app instance created')
    WorkflowShutdown = WorkflowSignal('Workflow Shutdown', 'Workflow shutdown')
    WorkflowAborted = WorkflowSignal('Workflow Aborted', 'Workflow aborted')
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
        """Gets an event from its string name

        Args:
            event_name (str): The name of the event

        Returns:
            WalkoffEvent: The WalkoffEvent associated with this string name
        """
        return getattr(cls, event_name, None)

    @classmethod
    def get_event_from_signal_name(cls, signal_name):
        """Gets an event from its signal name

        Args:
            signal_name (str): The name of the signal

        Returns:
            WalkoffEvent: The WalkoffEvent associated with the given signal name
        """
        return next((event for event in cls if event.signal_name == signal_name), None)

    def requires_data(self):
        """Does this event require additional data?

        Returns:
            bool
        """
        return (self in (WalkoffEvent.WorkflowShutdown,
                         WalkoffEvent.ActionExecutionError,
                         WalkoffEvent.ActionArgumentsInvalid,
                         WalkoffEvent.ActionExecutionSuccess,
                         WalkoffEvent.SendMessage))

    def send(self, sender, **kwargs):
        self.value.send(sender, **kwargs)

    def connect(self, func, weak=True):
        self.value.connect(func, weak=weak)
        return func

    def is_loggable(self):
        return self.value.is_loggable
