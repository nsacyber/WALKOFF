import logging
from weakref import WeakSet

import walkoff.config.config
from interfaces.util import convert_to_iterable
from walkoff.events import EventType
from walkoff.helpers import UnknownAppAction, UnknownApp

_logger = logging.getLogger(__name__)


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
            all_is_registered = ('all' in self._event_router[event]
                                 and self._event_router[event]['all'].is_registered(func))
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
            available_actions = set(walkoff.config.config.app_apis[app]['actions'].keys())
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
    """Routes and dispatches generic WalkoffEvents to their given callbacks

    Attributes:
        _router (dict(str: dict(WalkoffEvent: CallbackContainer))): The router
    """

    def __init__(self):
        self._router = {}

    def register_events(self, func, events, sender_ids=None, names=None, weak=True):
        """Registers an event for a given sender ID or name

        Args:
            func (func): Callback to register
            events (iterable(WalkoffEvent)): Events to register the callback to
            sender_ids (str|iterable(str), optional): IDs to register the callback to. Defaults to None
            names (str|iterable(str), optional): The names to register the callback to. Defaults to None
            weak (bool, optional): Should the callback be registered with a weak reference? Defaults to true
        """
        if sender_ids is None:
            sender_ids = []
        sender_ids = convert_to_iterable(sender_ids)
        if names is None:
            names = []
        names = convert_to_iterable(names)
        entry_ids = set(sender_ids) | set(names)
        if not entry_ids:
            entry_ids = ['all']
        for entry_id in entry_ids:
            self.__register_entry(entry_id, events, func, weak)

    def __register_entry(self, entry_id, events, func, weak):
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
        sender_name, sender_id = self.__get_sender_ids(data, event_)
        callbacks = self._get_callbacks(sender_id, sender_name, event_)

        for func in callbacks:
            try:
                args = (data,) if event_.event_type != EventType.controller else tuple()
                func(*args)
            except Exception as e:
                _logger.exception('Error calling interface event handler: {}'.format(e))

    @staticmethod
    def __get_sender_ids(data, event_):
        if event_.event_type != EventType.controller:
            sender_id = data['sender_id']
            sender_name = data['sender_name'] if 'sender_name' in data else None
        else:
            sender_id = EventType.controller.name
            sender_name = None
        return sender_name, sender_id

    def _get_callbacks(self, sender_id, sender_name, event):
        """Gets all the callbacks associated with a given sender ID, name, and event

        Args:
            sender_id (str): The ID of the sender of the event
            sender_name (str): The name of the sender of the event
            event (WalkoffEvent): The event

        Returns:
            set(func): The callbacks registered
        """
        all_callbacks = set()
        for sender_id_ in ('all', sender_id, sender_name):
            if self.__is_event_registered_to_sender(sender_id_, event):
                all_callbacks |= set(self._router[sender_id_][event])

        return all_callbacks

    def __is_event_registered_to_sender(self, sender_id, event):
        return (sender_id is not None
                and sender_id in self._router and event in self._router[sender_id])

    def is_registered(self, entry, event, func):
        """Is a function registered for a given entry ID and event?

        Args:
            entry (str): The entry ID of the callback
            event (WalkoffEvent): The event of the callback
            func (func): The callback

        Returns:
            bool: Is the function registered?
        """
        return entry in self._router and event in self._router[entry] and self._router[entry][event].is_registered(func)
