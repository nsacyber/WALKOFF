import logging
from copy import deepcopy
from functools import partial
from .util import validate_events, add_docstring
from .dispatchers import AppEventDispatcher, EventDispatcher
from .exceptions import UnknownEvent, InvalidEventHandler
from walkoff.events import WalkoffEvent, EventType
from walkoff.helpers import split_function_arg_names
import warnings
from walkoff.executiondb.representable import Representable

_logger = logging.getLogger(__name__)


class AppBlueprint(object):
    """Class to create blueprints for custom server endpoints in apps

    Attributes:
        blueprint (flask.Blueprint): The blueprint to register with Walkoff
        rule (str): The URL rule for the blueprint

    Args:
        blueprint (flask.Blueprint): The blueprint to register with Walkoff
        rule (str, optional): The URL rule for the blueprint. Defaults to /custominterfaces/<interface_name>/
    """
    def __init__(self, blueprint, rule=''):
        self.blueprint = blueprint
        self.rule = rule


class InterfaceEventDispatcher(object):
    """Primary dispatcher of events to interfaces

    This class generates event registration methods of the form "on_<signal_name>" on __new__ for all WalkoffEvents
    (provided that their EventType is not `other`).

    Note:
        This class is a singleton.

    Attributes:
        event_dispatcher (interfaces.disatchers.EventDispatcher): Router and dispatcher for WalkoffEvents
        app_action_dispatcher (interfaces.disatchers.AppEventDispatcher): Router and dispatcher for action WalkfoffEvents
    """

    __instance = None  # to make this class a singleton
    event_dispatcher = EventDispatcher()
    app_action_dispatcher = AppEventDispatcher()

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            for event in (event for event in WalkoffEvent if event.event_type != EventType.other and event != WalkoffEvent.SendMessage):
                dispatch_method = cls._make_dispatch_method(event)
                dispatch_partial = partial(dispatch_method, cls=cls)
                event.connect(dispatch_partial, weak=False)

                register_method = cls._make_register_method(event)
                event_name = event.signal_name
                event_name = event_name.replace(' ', '_')
                event_name = event_name.lower()
                register_method_name = 'on_{}'.format(event_name)
                setattr(cls, register_method_name, register_method)

            cls.__instance = super(InterfaceEventDispatcher, cls).__new__(cls)

        return cls.__instance

    @classmethod
    def _make_dispatch_method(cls, event):
        """Constructs a method used to connect to the WalkoffEvent and dispatch events

        Args:
            event (WalkoffEvent): The event to construct a dispatch method for

        Returns:
            func: The dispatch method
        """
        def dispatch_method(sender, **kwargs):
            if event.event_type != EventType.controller:
                if not isinstance(sender, dict) and isinstance(sender, Representable):
                    data = sender.read()
                else:
                    data = deepcopy(sender)
                additional_data = deepcopy(kwargs)
                additional_data.pop('cls', None)
                if 'data' in additional_data and 'workflow' in additional_data['data']:
                    additional_data['workflow'] = additional_data['data'].pop('workflow')
                    if not additional_data['data']:
                        additional_data.pop('data')
                data.update(additional_data)
                if 'id' in data:
                    data['sender_id'] = data.pop('id')
                if 'name' in data:
                    data['sender_name'] = data.pop('name')

            else:
                data = None
            cls.event_dispatcher.dispatch(event, data)
            if event.event_type == EventType.action:
                cls.app_action_dispatcher.dispatch(event, data)
        return dispatch_method

    @classmethod
    def _make_register_method(cls, event):
        """Constructs a method used by interface event handlers to connect to the dispatcher and register their callbacks

        Args:
            event (WalkoffEvent): Event used to construct the registration method

        Returns:
            func: The registration method for the event
        """
        @add_docstring(InterfaceEventDispatcher._make_on_walkoff_event_docstring(event))
        def on_event(cls, sender_ids=None, sender_uids=None, names=None, weak=True):
            if sender_uids:
                warnings.warn('"sender_uids" is a deprecated alias for "sender_ids". '
                              'This alias will be removed in version 0.9.0', PendingDeprecationWarning)
                if not sender_ids:
                    sender_ids = sender_uids

            def handler(func):
                InterfaceEventDispatcher._validate_handler_function_args(func, False)
                cls.event_dispatcher.register_events(func, {event}, sender_ids=sender_ids, names=names, weak=weak)
                return func  # Needed so weak references aren't deleted
            return handler

        @add_docstring(InterfaceEventDispatcher._make_on_walkoff_event_docstring(event))
        def on_controller_event(cls, weak=True):
            def handler(func):
                InterfaceEventDispatcher._validate_handler_function_args(func, True)
                cls.event_dispatcher.register_events(func, {event}, weak=weak)
                return func
            return handler

        return on_event if event.event_type != EventType.controller else on_controller_event

    @classmethod
    def on_app_actions(cls, app, actions='all', events='all', device_ids='all', weak=True):
        """Decorator to register a function as a callback for a given app, action(s), event(s), and device(s)

        Args:
            app (str): The app whose events should be handled
            actions (str|iterable(str), optional): The actions whose events should be handled, Defaults to all actions
            events (str|WalkoffEvent|iterable(str|WalkoffEvent)): The events which should be handled. an use either a
                WalkoffEvent or its signal name. Defaults to all action-type events
            device_ids (int|iterable(int), optional): The IDs of the devices whose events should be handled. Defaults to
                all devices
            weak (bool, optional): Should the callback be registered as a weak function? Defaults to True. Warning!
                Setting this to False could causes memory leaks.

        Returns:
            func: The original function

        Raises:
            UnknownEvent: If an unknown or non-action event is set for the handler
            InvalidEventHandler: If the wrapped function does not have exactly one argument
        """
        available_events = {event for event in WalkoffEvent if event.event_type == EventType.action and event != WalkoffEvent.SendMessage}
        events = validate_events(events, available_events)

        def handler(func):
            InterfaceEventDispatcher._validate_handler_function_args(func, False)
            cls.app_action_dispatcher.register_app_actions(func, app, actions=actions, events=events, device_ids=device_ids,
                                                           weak=weak)
            return func
        return handler

    @classmethod
    def on_walkoff_events(cls, events, sender_ids=None, sender_uids=None, names=None, weak=True):
        """Decorator to register a function as a callback for given WalkoffEvent(s)

        Args:
            events (str|WalkoffEvent|iterable(str|WalkoffEvent)): The events which should be handled. an use either a
                WalkoffEvent or its signal name. Defaults to all action-type events
            sender_uids (str|iterable(str), optional): Deprecated alias for "sender_ids". This will be removed in 0.8.0
            sender_ids (str|iterable(str), optional): The IDs of the sender which will cause this callback to trigger.
            names (str|iterable(str), optional): The names of the sender to will cause this callback to trigger. Note
                that unlike IDS, these are not guaranteed to be unique.
            weak (bool, optional): Should the callback be registered as a weak function? Defaults to True. Warning!
                Setting this to False could causes memory leaks.

        Returns:
            func: The original function wrapped

         Raises:
            UnknownEvent: If an unknown event is set for the handler
            ValueError: If a mix of controller and non-controller events are set for the handler
            InvalidEventHandler: If the wrapped function does not have the correct number of arguments
        """
        if sender_uids:
            warnings.warn('"sender_uids" is a deprecated alias for "sender_ids". This will be removed in 0.9.0',
                          PendingDeprecationWarning)
            if not sender_ids:
                sender_ids = sender_uids
        events = validate_events(events)
        are_controller_events = InterfaceEventDispatcher._all_events_are_controller(events)
        if are_controller_events:
            if sender_ids or names:
                _logger.warning('Sender IDs and names are invalid for controller events')
            sender_ids = EventType.controller.name

        def handler(func):
            InterfaceEventDispatcher._validate_handler_function_args(func, are_controller_events)
            cls.event_dispatcher.register_events(func, events, sender_ids=sender_ids, names=names, weak=weak)
            return func
        return handler

    @classmethod
    def _clear(cls):
        """Clears all the registered callbacks
        """
        cls.event_dispatcher = EventDispatcher()
        cls.app_action_dispatcher = AppEventDispatcher()

    @staticmethod
    def _validate_handler_function_args(func, is_controller):
        """Validates a handler function by checking how many arguments it has

        Args:
            func (func): The function to check
            is_controller (bool): Is the function intended to handle controller events?

        Raises:
            InvalidEventHandler: If the number of arguments is incorrect
        """
        args = split_function_arg_names(func)
        print(func.__name__)
        print(args)

        num_args = len(args['args'])
        is_generic = 'varargs' in args and not num_args  # allow (*args)
        print(is_generic)
        if not is_generic:
            if is_controller:
                if num_args != 0:
                    raise InvalidEventHandler('Handlers for controller events take no arguments')
            elif num_args != 1:
                raise InvalidEventHandler('Handlers for events non-controller events take one argument')

    @staticmethod
    def _all_events_are_controller(events):
        """Are all the events controller type?

        Args:
            events (iterable(WalkoffEvent)): The events to check

        Returns:
            bool: True if all the events are controller type. False otherwise

        Raises:
            ValueError: If a mix of controller type and non-controller type events are found
        """
        if any(event.event_type == EventType.controller for event in events):
            if not all(event.event_type == EventType.controller for event in events):
                raise ValueError('Cannot combine controller events and non-controller events')
            return True
        return False

    @staticmethod
    def _make_on_walkoff_event_docstring(event):
        """Makes a docstring for the `on_<event>` registration methods

        Args:
            event (WalkoffEvent): The event the handler function is handling

        Returns:
            str: The docstring for the registration method
        """
        args_string = 'Args:\n'
        is_controller = event.event_type == EventType.controller
        if not is_controller:
            args_string = ('{}'
                '\tsender_uids (str|iterable(str), optional): Deprecated alias for "sender_ids" this will be removed in 0.9.0\n'
                '\tsender_ids (str|iterable(str), optional): The IDs of the sender which will cause this callback to trigger.\n'
                '\tnames (str|iterable(str), optional): The names of the sender to will cause this callback to trigger. Note that unlike '
                'IDS, these are not guaranteed to be unique.\n'.format(args_string))
        args_string = ('{}\tweak (boolean, optional): Should the callback persist even if function leaves scope? Warning! '
                       'Could cause memory leaks'.format(args_string))
        return '''

Creates a callback for the {0} WalkoffEvent. Requires that the function being decorated have the signature `{1}`.

{2}
Raises:
    InvalidEventHandler: If the wrapped function has the incorrect number of arguments for the event type
'''.format(event.signal_name,
           'def handler(data)' if not is_controller else 'def handler()', args_string)


dispatcher = InterfaceEventDispatcher()
"""InterfaceEventDispatcher: The global dispatcher to use when registering interface event handlers
"""
