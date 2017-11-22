import logging
from copy import deepcopy
from functools import partial
from weakref import WeakSet

from six import string_types

import core.config.config
from core.events import WalkoffEvent, EventType
from core.helpers import UnknownApp, UnknownAppAction, get_function_arg_names

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


def convert_events(events):
    """Converts events from signal names to WalkoffEvents

    Args:
        events (str|WalkoffEvent|iterable(str|WalkoffEvent)): The events to convert

    Returns:
        set(WalkoffEvent): The converted events

    Raises:
        UnknownEvent: If any signal name has no corresponding WalkoffEvent
    """
    converted_events = set()
    for event in convert_to_iterable(events):
        if isinstance(event, WalkoffEvent):
            converted_events.add(event)
        else:
            converted_event = WalkoffEvent.get_event_from_signal_name(event)
            if converted_event is None:
                raise UnknownEvent(event)
            converted_events.add(converted_event)
    return converted_events


def validate_events(events='all', allowed_events=set(WalkoffEvent)):
    """Validates a set of events against allowed events. Converts strings to events if possible.

    Args:
        events (str|WalkoffEvent|iterable(str|WalkoffEvent), optional): The event or events to validate.
            Defaults to all events
        allowed_events (iterable(WalkoffEvent), optional): The allowed events. Defaults to all WalkoffEvents

    Returns:
        set(WalkoffEvent): The converted set of events.

    Raises:
        UnknownEvent: If some events passed in are not in available_events
    """
    if events == 'all':
        return set(allowed_events)
    converted_events = convert_events(events)
    if set(converted_events) - set(allowed_events):
        raise UnknownEvent(set(converted_events) - set(allowed_events))
    return converted_events


def add_docstring(docstring):
    """Decorator to add a docstring dynamically to a function

    Args:
        docstring (str): The string to use as the docstring

    Returns:
        func: The function with the added docstring
    """
    def wrapper(func):
        func.__doc__ = docstring
        return func
    return wrapper


def convert_to_iterable(elements):
    """Converts an element or elements to list if it not already iterable

    Args:
        elements (:obj:|iterable(:obj:)): The object to convert to an iterable if necessary

    Returns:
        iterable: A list containing only the element passed in if the element was a non-string non-iterable.
            The original iterable otherwise
    """
    try:
        if isinstance(elements, string_types):
            return [elements]
        iter(elements)
        return elements
    except TypeError:
        return [elements]


class UnknownEvent(Exception):
    """Exception thrown when an unknown or unallowed event(s) is encountered

    Attributes:
        message (str): The error message

    Args:
        events (str|WalkoffEvent|iterable(str|WalkoffEvent)): The unallowed event(s)
    """
    def __init__(self, events):
        self.message = 'Unknown event(s) {}'.format(events if isinstance(events, string_types) else list(events))
        super(Exception, self).__init__(self.message)


class InvalidEventHandler(Exception):
    """Exception thrown when an invalid function is intended to be used as an event handler

    Attributes:
        message (str): The error message

    Args:
        message (str): The error message
    """
    def __init__(self, message):
        self.message = message
        super(Exception, self).__init__(self.message)


class CallbackContainer(object):
    """A container holding both strong and weak references to callbacks

    Attributes:
        weak (WeakSet(func)): Weak references to callbacks
        strong (set(func)): Strong references to callbacks

    Args:
        weak (iterable(func), optional): The initial functions to add as weak references. Defaults to None
        strong (iterable(func), optional): The initial functions to add as strong references. Defaults to None
    """
    def __init__(self, weak=None, strong=None):
        self.weak = WeakSet() if weak is None else WeakSet(weak)
        self.strong = set() if strong is None else set(strong)

    def register(self, func, weak=True):
        """Registers a function in the container

        Args:
            func (func): The function to register
            weak (bool, optional): Should the reference be a weak reference? Defaults to True
        """
        if weak:
            self.weak.add(func)
        else:
            self.strong.add(func)

    def __iter__(self):
        for weak_callback in self.weak:
            yield weak_callback
        for strong_callback in self.strong:
            yield strong_callback
        raise StopIteration

    def iter_strong(self):
        """Iterates over all the strong references

        Yields:
            func: The next callback with a strong reference
        """
        for strong_callback in self.strong:
            yield strong_callback
        raise StopIteration

    def iter_weak(self):
        """Iterates over all the weak references

        Yields:
            func: The next callback with a weak reference
        """
        for weak_callback in self.weak:
            yield weak_callback
        raise StopIteration

    def is_registered(self, func):
        """Is a function registered?

        Args:
            func: The function to check

        Returns:
            bool: Is the function registered?
        """
        return func in self.weak or func in self.strong


class AppActionEventDispatcher(object):
    """Container for routing and dispatching action events for a specific app and action

    Attributes:
        app (str): The app associated with this dispatcher
        action (str): The action associated with this dispatcher
        _event_router(dict(WalkoffEvent: dict(int|str: CallbackContainer))): The router for events

    Args:
        app (str): The app associated with this dispatcher
        action (str): The action associated with this dispatcher
    """
    def __init__(self, app, action):
        self.app = app
        self.action = action
        self._event_router = {}

    def register_event(self, event, device_ids, func, weak=True):
        """Registers an event and device_ids to a function

        Args:
            event (WalkoffEvent): The event to register
            device_ids: (str|iterable(int)): The device IDs to register to. Specifying 'all' will always trigger
                regardless of device ID passed to dispatch()
            func (func): Function to register
            weak: (bool, optional): Should the reference to the function be weak? Defaults to True
        """
        if event not in self._event_router:
            self._event_router[event] = {}
        if device_ids == 'all':
            self._register_event_for_device_id(event, 'all', func, weak)
        else:
            device_ids = convert_to_iterable(device_ids)
            for device_id in device_ids:
                self._register_event_for_device_id(event, device_id, func, weak)

    def dispatch(self, event_, data):
        """Dispatches an event to all registered callbacks

        Note:
            All exceptions thrown by callbacks will be caught and logged, but not handled

        Args:
            event_ (WalkoffEvent): The event to dispatch
            data (dict): The data to send to the functions
        """
        for callback in self._get_callbacks(event_, data['device_id']):
            try:
                callback(data)
            except Exception as e:
                _logger.exception('Exception in calling interface event handler: {}'.format(callback))

    def _register_event_for_device_id(self, event, device_id, func, weak):
        """Registers a function to a specific event and device ID

        Args:
            event (WalkoffEvent): The event to register
            device_id (str|int): The device ID to register the function to. Specifying 'all' will always trigger
                regardless of device ID passed to dispatch()
            func (func): Function to register
            weak: (bool): Should the reference to the function be weak?
        """
        if device_id not in self._event_router[event]:
            self._event_router[event][device_id] = CallbackContainer()
        self._event_router[event][device_id].register(func, weak)

    def _get_callbacks(self, event, device_id):
        """Gets the callbacks associated with an event and device ID

        Args:
            event (WalkoffEvent): The event whose callbacks to retrieve
            device_id (str|int): The device ID whose callbacks to receive

        Yields:
            func: The next callback
        """
        if event in self._event_router:
            for callback in self._event_router[event].get('all', []):
                yield callback
            if device_id != 'all':
                for callback in self._event_router[event].get(device_id, []):
                    yield callback
        raise StopIteration

    def is_registered(self, event, device_id, func):
        """Is a function registered?

        Args:
            event (WalkoffEvent): The event to check
            device_id (str|int): The device ID to check
            func (func): The function to check

        Returns:
            bool: Is the function registered?
        """
        if event in self._event_router:
            all_is_registered = 'all' in self._event_router[event] and self._event_router[event]['all'].is_registered(func)
            if device_id == 'all':
                return all_is_registered
            return (all_is_registered or
                    (device_id in self._event_router[event]
                     and self._event_router[event][device_id].is_registered(func)))
        return False


class AppEventDispatcher(object):
    """Object which routes and dispatches action events

    Attributes:
        _router (dict(str: dict(str: AppActionEventDispatcher))): The router
    """
    def __init__(self):
        self._router = {}

    def register_app_actions(self, func, app, events, actions='all', device_ids='all', weak=True):
        """Registers an callback for a given event, app, action, and device ID

        Args:
            func (func): Function to register
            app (str): The app to register the callback to
            events (iterable(WalkoffEvent)): The events to register to callback to
            actions (str|iterable(str), optional): The actions to register the callback to. Defaults to 'all',
                meaning all actions
            device_ids (str|int|iterable(int), optional): The devices to register the callback to. Defaults to 'all'
                meaning all devices
            weak (bool, optional): Should the function be registered as a weak reference? Defaults to True

        Raises:
            UnknownApp: If the app specified is not found in all known app APIs or the app has no actions
            UnknownAppAction: If the action is not found in the give app's actions
        """
        actions = AppEventDispatcher.validate_app_actions(app, actions)

        if app not in self._router:
            self._router[app] = {}
        for action in actions:
            if action not in self._router[app]:
                self._router[app][action] = AppActionEventDispatcher(app, action)
            for event in events:
                self._router[app][action].register_event(event, device_ids, func, weak=weak)

    def dispatch(self, event_, data):
        """Dispatches an event to all registered callbacks

        Note:
            All exceptions thrown by callbacks will be caught and logged, but not handled

        Args:
            event_ (WalkoffEvent): The event to dispatch
            data (dict): The data to send to the callbacks
        """
        app_name = data['app_name']
        action_name = data['action_name']
        if app_name in self._router and action_name in self._router[app_name]:
            self._router[app_name][action_name].dispatch(event_, data)

    @staticmethod
    def validate_app_actions(app, actions):
        """Validates that an app's actions are valid, meaning that they exist in a defined app API

        Args:
            app (str): The app to validate
            actions (str): The action to validate

        Returns:
            set(str): The actions. Expanded to all known actions if `action` was 'all'

         Raises:
            UnknownApp: If the app specified is not found in all known app APIs or the app has no actions
            UnknownAppAction: If the action is not found in the give app's actions
        """
        try:
            available_actions = set(core.config.config.app_apis[app]['actions'].keys())
            if actions == 'all':
                return available_actions
            actions = set(convert_to_iterable(actions))
            if actions - available_actions:
                message = 'Unknown actions for app {0}: {1}'.format(app, list(set(actions) - set(available_actions)))
                _logger.error(message)
                raise UnknownAppAction(app, actions)
            return actions
        except KeyError:
            message = 'Unknown app {} or app has no actions'.format(app)
            _logger.exception(message)
            raise UnknownApp(app)

    def is_registered(self, app, action, event, device, func):
        """Is a given callback registered

        Args:
            app (str): The callback's app
            action (str): The callback's action
            event (WalkoffEvent): The callback's event
            device (str|int): The callback's device ID
            func (func): The callback

        Returns:
            bool: Is the callback registered?
        """
        return (app in self._router and action in self._router[app]
                and self._router[app][action].is_registered(event, device, func))


class EventDispatcher(object):
    """Routes as disatches generic WalkoffEvents to their given callbacks

    Attributes:
        _router (dict(str: dict(WalkoffEvent: CallbackContainer))): The router
    """
    def __init__(self):
        self._router = {}

    def register_events(self, func, events, sender_uids=None, names=None, weak=True):
        """Registers an event for a given sender UID or name

        Args:
            func (func): Callback to register
            events (iterable(WalkoffEvent)): Events to register the callback to
            sender_uids (str|iterable(str), optional): UIDs to register the callback to. Defaults to None
            names (str|iterable(str), optional): The names to register the callback to. Defaults to None
            weak (bool, optional): Should the callback be registered with a weak reference? Defaults to true
        """
        if sender_uids is None:
            sender_uids = []
        sender_uids = convert_to_iterable(sender_uids)
        if names is None:
            names = []
        names = convert_to_iterable(names)
        entry_ids = set(sender_uids) | set(names)
        if not entry_ids:
            raise ValueError('Either sender_uid or name must specified')
        for entry_id in entry_ids:
            if entry_id not in self._router:
                self._router[entry_id] = {}
            for event in events:
                if event not in self._router[entry_id]:
                    self._router[entry_id][event] = CallbackContainer()
                self._router[entry_id][event].register(func, weak=weak)

    def dispatch(self, event_, data):
        """Dispatches an event to all its registered callbacks

        Note:
            All exceptions thrown by callbacks will be caught and logged, but not handled

        Args:
            event_ (WalkoffEvent): The event to dispatch
            data (dict): The data to send to all the events
        """
        if event_.event_type != EventType.controller:
            sender_uid = data['sender_uid']
            sender_name = data['sender_name'] if 'sender_name' in data else None
        else:
            sender_uid = EventType.controller.name
            sender_name = None
        callbacks = self._get_callbacks(sender_uid, sender_name, event_)
        for func in callbacks:
            try:
                if event_.event_type != EventType.controller:
                    func(data)
                else:
                    func()
            except Exception as e:
                _logger.exception('Error calling interface event handler: {}'.format(e))

    def _get_callbacks(self, sender_uid, sender_name, event):
        """Gets all the callbacks associated with a given sender UID, name, and event

        Args:
            sender_uid (str): The UID of the sender of the event
            sender_name (str): The name of the sender of the event
            event (WalkoffEvent): The event

        Returns:
            set(func): The callbacks registered
        """
        all_callbacks = set()
        if sender_uid in self._router and event in self._router[sender_uid]:
            all_callbacks |= set(self._router[sender_uid][event])

        if sender_name is not None and sender_name in self._router and event in self._router[sender_name]:
            all_callbacks |= set(self._router[sender_name][event])
        return all_callbacks

    def is_registered(self, entry, event, func):
        """Is a function registered for a given entry ID and event?

        Args:
            entry (str): The entry ID of the callback
            event (WalkoffEvent): The event of the callback
            func (func): The callback

        Returns:
            bool: Is the function registred?
        """
        return entry in self._router and event in self._router[entry] and self._router[entry][event].is_registered(func)


class InterfaceEventDispatcher(object):
    """Primary dispatcher of events to interfaces

    This class generates event registration methods of the form "on_<signal_name>" on __new__ for all WalkoffEvents
    (provided that their EventType is not `other`).

    Note:
        This class is a singleton.

    Attributes:
        event_dispatcher (EventDispatcher): Router and dispatcher for WalkoffEvents
        app_action_dispatcher (AppEventDispatcher): Router and dispatcher for action WalkfoffEvents
    """

    __instance = None  # to make this class a singleton
    event_dispatcher = EventDispatcher()
    app_action_dispatcher = AppEventDispatcher()

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            for event in (event for event in WalkoffEvent if event.event_type != EventType.other):
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
                data = deepcopy(sender)
                additional_data = deepcopy(kwargs)
                additional_data.pop('cls', None)
                data.update(additional_data)
                if 'uid' in data:
                    data['sender_uid'] = data.pop('uid')
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
        def on_event(cls, sender_uids=None, names=None, weak=True):
            def handler(func):
                InterfaceEventDispatcher._validate_handler_function_args(func, False)
                cls.event_dispatcher.register_events(func, {event}, sender_uids=sender_uids, names=names, weak=weak)
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
        available_events = {event for event in WalkoffEvent if event.event_type == EventType.action}
        events = validate_events(events, available_events)

        def handler(func):
            InterfaceEventDispatcher._validate_handler_function_args(func, False)
            cls.app_action_dispatcher.register_app_actions(func, app, actions=actions, events=events, device_ids=device_ids,
                                                           weak=weak)
            return func
        return handler

    @classmethod
    def on_walkoff_events(cls, events, sender_uids=None, names=None, weak=True):
        """Decorator to register a function as a callback for given WalkoffEvent(s)

        Args:
            events (str|WalkoffEvent|iterable(str|WalkoffEvent)): The events which should be handled. an use either a
                WalkoffEvent or its signal name. Defaults to all action-type events
            sender_uids (str|iterable(str), optional): The UIDs of the sender which will cause this callback to trigger.
            names (str|iterable(str), optional): The names of the sender to will cause this callback to trigger. Note
                that unlike UIDS, these are not guaranteed to be unique.
            weak (bool, optional): Should the callback be registered as a weak function? Defaults to True. Warning!
                Setting this to False could causes memory leaks.

        Returns:
            func: The original function wrapped

         Raises:
            UnknownEvent: If an unknown event is set for the handler
            ValueError: If a mix of controller and non-controller events are set for the handler
            InvalidEventHandler: If the wrapped function does not have the correct number of arguments
        """
        events = validate_events(events)
        are_controller_events = InterfaceEventDispatcher._all_events_are_controller(events)
        if are_controller_events:
            if sender_uids or names:
                _logger.warning('Sender UIDs and names are invalid for controller events')
            sender_uids = EventType.controller.name

        def handler(func):
            InterfaceEventDispatcher._validate_handler_function_args(func, are_controller_events)
            cls.event_dispatcher.register_events(func, events, sender_uids=sender_uids, names=names, weak=weak)
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
        num_args = len(get_function_arg_names(func))
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
                '\tsender_uids (str|iterable(str), optional): The UIDs of the sender which will cause this callback to trigger.\n'
                '\tnames (str|iterable(str), optional): The names of the sender to will cause this callback to trigger. Note that unlike '
                'UIDS, these are not guaranteed to be unique.\n'.format(args_string))
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
