from core.events import WalkoffEvent, EventType
import core.config.config
import logging
from six import string_types

_logger = logging.getLogger(__name__)


class AppWidgetBlueprint(object):
    """
    Class to create blueprints for custom server endpoints in apps
    """
    def __init__(self, blueprint, rule=''):
        self.blueprint = blueprint
        self.rule = rule


AppBlueprint = AppWidgetBlueprint

# wrapper for waiting for step/workflow to complete, waiting for generic event to happen with a UID

'''
def on_walkoff_event(sender_uid=None)
def on_workflow_started(sender_uid=None, name=None)  # raise error if neither of these are filled in
def on_workflow_ended
def on_action_started
def on_action_ended
def on_action_error
def on_app_action(appname, actions='all' or ['list of action names'], device_name=None)


these callbacks should work on class decorators
'''


def convert_events_from_names(events):
    converted_events = set()
    for event in events:
        if isinstance(event, WalkoffEvent):
            converted_events.add(event)
        else:
            converted_event = WalkoffEvent.get_event_from_signal_name(event)
            if converted_event is None:
                raise UnknownEvent(event)
            converted_events.add(converted_event)
    return converted_events


def validate_events(events='all', available_events=set(WalkoffEvent)):
    if events == 'all':
        return available_events
    converted_events = convert_events_from_names(events)
    if set(converted_events) - available_events:
        raise UnknownEvent(set(events) - set(available_events))
    return converted_events


class UnknownEvent(Exception):
    def __init__(self, event):
        self.message = 'Unknown event(s) {}'.format(event)
        super(Exception, self).__init__(self.message)


class AppActionEventRouter(object):
    def __init__(self, app, action):
        self.app = app
        self.action = action
        self.events = {}
        self.devices = []

    def register_event(self, event, func):
        if event not in self.events:
            self.events[event] = [func]
        elif func not in self.events[event]:
            self.events[event].append(func)


class AppEventRouter(object):
    def __init__(self):
        self._router = {}

    def register_app_actions(self, func, app, actions='all', events='all'):
        actions = AppEventRouter.validate_app_actions(app, actions)
        available_events = {event for event in WalkoffEvent
                            if event.event_type in (EventType.action, EventType.condition, EventType.transform)}
        events = validate_events(events, available_events)
        if app not in self._router:
            self._router[app] = {}
        for action in actions:
            if action not in self._router[app]:
                self._router[app][action] = AppActionEventRouter(app, action)
            for event in events:
                self._router[app][action].register_events(event, func)

    @staticmethod
    def validate_app_actions(app, actions):
        try:
            available_actions = core.config.config.app_apis[app]['actions'].keys()
            if actions == 'all':
                return available_actions
            if set(actions) - set(available_actions):
                message = 'Unknown actions for app {0}: {1}'.format(app, list(set(actions) - set(available_actions)))
                _logger.error(message)
                raise ValueError(message)
            return actions
        except KeyError:
            message = 'Unknown app {} or app has no actions'.format(app)
            _logger.exception(message)
            raise


class EventRouter(object):
    def __init__(self):
        self._router = {}

    def register_events(self, func, event_names, sender_uids=None, names=None):
        if sender_uids is None:
            sender_uids = []
        elif isinstance(sender_uids, string_types):
            sender_uids = [sender_uids]
        if names is None:
            names = []
        elif isinstance(names, string_types):
            names = [names]
        if isinstance(event_names, string_types):
            event_names = [event_names]
        if not (sender_uids or names):
            raise ValueError('Either sender_uid or name must specified')

        entry_ids = set(sender_uids) | set(names)
        events = validate_events(event_names)
        for entry_id in entry_ids:
            if entry_id not in self._router:
                self._router[entry_id] = {}
            for event in events:
                if event not in self._router[entry_id]:
                    self._router[entry_id][event] = [func]
                elif func not in self._router[entry_id][event]:
                    self._router[entry_id][event].append(func)

    def dispatch(self, event_, sender, **kwargs):
        callbacks = self.__get_callbacks(sender, event_)
        for func in callbacks:
            func(sender, **kwargs)

    def __get_callbacks(self, sender, event):
        if sender.uid in self._router and event in self._router[sender.uid]:
            return self._router[sender.uid][event]
        elif hasattr(sender, 'name') and sender.name in self._router and event in self._router[sender.name]:
            return self._router[sender.name][event]
        else:
            return []


class InterfaceEventDispatch(object):

    __instance = None  # to make this class a singleton
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(InterfaceEventDispatch, cls).__new__(cls)
        return cls.__instance

    def __init__(self):

        self._app_action_router = AppEventRouter()
        self._event_router = EventRouter()
        for event in WalkoffEvent:
            event_name = event.signal_name

            dispatch_method = self._make_dispatch_method(event)
            register_method = self._make_register_method(event_name)

            event_name = event_name.replace(' ', '_')
            event_name = event_name.lower()
            dispatch_method_name = '_dispatch_{}_event'.format(event_name)
            register_method_name = 'on_{}'.format(event_name)
            event_name = '__{}_callback'
            setattr(self, dispatch_method_name, dispatch_method)
            setattr(self, register_method_name, register_method)

            def callback_function(sender, **kwargs):
                getattr(self, dispatch_method_name)(self, sender, **kwargs)

            setattr(self, event_name, callback_function)
            event.connect(callback_function, weak=False)

    def on_app_actions(self, app, actions='all', events='all'):
        def handler(func):
            self._app_action_router.register_app_actions(func, app, actions, events)
        return handler

    def on_walkoff_events(self, events='all', sender_uids=None, names=None):
        def handler(func):
            self._event_router.register_events(func, events, sender_uids, names)
        return handler

    def _make_dispatch_method(self, event):
        def dispatch_method(self, sender, **kwargs):
            self._event_router.dispatch(event, sender, **kwargs)
        return dispatch_method

    def _make_register_method(self, event_name):
        def on_workflow_event(sender_uids=None, names=None):
            def handler(func):
                self._event_router.register_events(func, event_name, sender_uids, names)
            return handler

        return on_workflow_event


dispatcher = InterfaceEventDispatch()


@dispatcher.on_workflow_shutdown(sender_uids='6645b2d61a514cbd8c8ce1094fa63be1')
def x(sender, **kwargs):
    print('CALLED')
    print(kwargs)