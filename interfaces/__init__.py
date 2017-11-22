from core.events import WalkoffEvent, EventType
import core.config.config
from core.helpers import UnknownApp, UnknownAppAction, get_function_arg_names
import logging
from six import string_types
from weakref import WeakSet
from google.protobuf.json_format import MessageToDict
from functools import partial
_logger = logging.getLogger(__name__)
from copy import deepcopy

class AppWidgetBlueprint(object):
    """
    Class to create blueprints for custom server endpoints in apps
    """
    def __init__(self, blueprint, rule=''):
        self.blueprint = blueprint
        self.rule = rule


AppBlueprint = AppWidgetBlueprint


def convert_events(events):
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


def validate_events(events='all', available_events=set(WalkoffEvent)):
    if events == 'all':
        return available_events
    converted_events = convert_events(events)
    if set(converted_events) - set(available_events):
        raise UnknownEvent(set(converted_events) - set(available_events))
    return converted_events


def add_docstring(docstring):
    def wrapper(func):
        func.__doc__ = docstring
        return func
    return wrapper


def convert_to_iterable(elements):
    try:
        if isinstance(elements, string_types):
            return [elements]
        iter(elements)
        return elements
    except TypeError:
        return [elements]


class UnknownEvent(Exception):
    def __init__(self, event):
        self.message = 'Unknown event(s) {}'.format(event if isinstance(event, string_types) else list(event))
        super(Exception, self).__init__(self.message)


class InvalidEventHandler(Exception):
    def __init__(self, message):
        self.message = message
        super(Exception, self).__init__(self.message)


class CallbackContainer(object):
    def __init__(self, weak=None, strong=None):
        self.weak = WeakSet() if weak is None else WeakSet(weak)
        self.strong = set() if strong is None else set(strong)

    def register(self, func, weak=True):
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
        for strong_callback in self.strong:
            yield strong_callback
        raise StopIteration

    def iter_weak(self):
        for weak_callback in self.weak:
            yield weak_callback
        raise StopIteration

    def is_registered(self, func):
        return func in self.weak or func in self.strong


class AppActionEventDispatcher(object):
    def __init__(self, app, action):
        self.app = app
        self.action = action
        self._event_router = {}

    def register_event(self, event, device_ids, func, weak=True):
        if event not in self._event_router:
            self._event_router[event] = {}
        if device_ids == 'all':
            self._register_event_for_device_id(event, 'all', func, weak)
        else:
            device_ids = convert_to_iterable(device_ids)
            for device_id in device_ids:
                self._register_event_for_device_id(event, device_id, func, weak)

    def dispatch(self, event_, data):
        for callback in self._get_callbacks(event_, data['device_id']):
            try:
                callback(data)
            except Exception as e:
                _logger.exception('Exception in calling interface event handler: {}'.format(callback))

    def _register_event_for_device_id(self, event, device_id, func, weak):
        if device_id not in self._event_router[event]:
            self._event_router[event][device_id] = CallbackContainer()
        self._event_router[event][device_id].register(func, weak)

    def _get_callbacks(self, event, device_id):
        if event in self._event_router:
            for callback in self._event_router[event].get('all', []):
                yield callback
            if device_id != 'all':
                for callback in self._event_router[event].get(device_id, []):
                    yield callback
        raise StopIteration

    def is_registered(self, event, device_id, func):
        if event in self._event_router:
            all_is_registered = 'all' in self._event_router[event] and self._event_router[event]['all'].is_registered(func)
            if device_id == 'all':
                return all_is_registered
            return (all_is_registered or
                    (device_id in self._event_router[event]
                     and self._event_router[event][device_id].is_registered(func)))
        return False


class AppEventDispatcher(object):
    def __init__(self):
        self._router = {}

    def register_app_actions(self, func, app, events, actions='all', devices='all', weak=True):
        """

        Args:
            func (func): Function to register
            app (str): The app to register the callback to
            actions (str|iterable(str), optional): Something
            events (iterable(str|WalkoffEvent, optional): The actions to look for
            devices
        """
        actions = AppEventDispatcher.validate_app_actions(app, actions)

        if app not in self._router:
            self._router[app] = {}
        for action in actions:
            if action not in self._router[app]:
                self._router[app][action] = AppActionEventDispatcher(app, action)
            for event in events:
                self._router[app][action].register_event(event, devices, func, weak=weak)

    def dispatch(self, event_, data):
        app_name = data['app_name']
        action_name = data['action_name']
        if app_name in self._router and action_name in self._router[app_name]:
            self._router[app_name][action_name].dispatch(event_, data)

    @staticmethod
    def validate_app_actions(app, actions):
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
        return (app in self._router and action in self._router[app]
                and self._router[app][action].is_registered(event, device, func))


class EventDispatcher(object):
    def __init__(self):
        self._router = {}

    def register_events(self, func, events, sender_uids=None, names=None, weak=True):
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
        all_callbacks = set()
        if sender_uid in self._router and event in self._router[sender_uid]:
            all_callbacks |= set(self._router[sender_uid][event])

        if sender_name is not None and sender_name in self._router and event in self._router[sender_name]:
            all_callbacks |= set(self._router[sender_name][event])
        return all_callbacks

    def is_registered(self, entry, event, func):
        return entry in self._router and event in self._router[entry] and self._router[entry][event].is_registered(func)


class InterfaceEventDispatcher(object):

    __instance = None  # to make this class a singleton
    event_router = EventDispatcher()
    app_action_router = AppEventDispatcher()

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
        def dispatch_method(sender, **kwargs):
            if event.event_type != EventType.controller:
                data = deepcopy(sender)
                kwargs.pop('cls', None)
                data.update(kwargs)
                if 'uid' in data:
                    data['sender_uid'] = data.pop('uid')
                if 'name' in data:
                    data['sender_name'] = data.pop('name')
            else:
                data = None
            cls.event_router.dispatch(event, data)
            if event.event_type == EventType.action:
                cls.app_action_router.dispatch(event, data)
        return dispatch_method

    @classmethod
    def _make_register_method(cls, event):
        @add_docstring(InterfaceEventDispatcher._make_on_walkoff_event_docstring(event))
        def on_event(cls, sender_uids=None, names=None, weak=True):
            def handler(func):
                InterfaceEventDispatcher._validate_handler_function_args(func, False)
                cls.event_router.register_events(func, {event}, sender_uids=sender_uids, names=names, weak=weak)
                return func  # Needed so weak references aren't deleted
            return handler

        @add_docstring(InterfaceEventDispatcher._make_on_walkoff_event_docstring(event))
        def on_controller_event(cls, weak=True):
            def handler(func):
                InterfaceEventDispatcher._validate_handler_function_args(func, True)
                cls.event_router.register_events(func, {event}, weak=weak)
                return func
            return handler

        return on_event if event.event_type != EventType.controller else on_controller_event

    @classmethod
    def on_app_actions(cls, app, actions='all', events='all', devices='all', weak=True):
        available_events = {event for event in WalkoffEvent if event.event_type == EventType.action}
        events = validate_events(events, available_events)
        def handler(func):
            InterfaceEventDispatcher._validate_handler_function_args(func, False)
            cls.app_action_router.register_app_actions(func, app, actions=actions, events=events, devices=devices,
                                                       weak=weak)
            return func
        return handler

    @classmethod
    def on_walkoff_events(cls, events, sender_uids=None, names=None, weak=True):
        events = validate_events(events)
        are_controller_events = InterfaceEventDispatcher._all_events_are_controller(events)
        if are_controller_events:
            if sender_uids or names:
                _logger.warning('Sender UIDs and names are invalid for controller events')
            sender_uids = EventType.controller.name

        def handler(func):
            InterfaceEventDispatcher._validate_handler_function_args(func, are_controller_events)
            cls.event_router.register_events(func, events, sender_uids=sender_uids, names=names, weak=weak)
            return func
        return handler

    @classmethod
    def _clear(cls):
        cls.event_router = EventDispatcher()
        cls.app_action_router = AppEventDispatcher()

    @staticmethod
    def _validate_handler_function_args(func, is_controller):
        num_args = len(get_function_arg_names(func))
        if is_controller:
            if num_args != 0:
                raise InvalidEventHandler('Handlers for controller events take no arguments')
        elif num_args != 1:
            raise InvalidEventHandler('Handlers for events non-controller events take one argument')

    @staticmethod
    def _all_events_are_controller(events):
        if any(event.event_type == EventType.controller for event in events):
            if not all(event.event_type == EventType.controller for event in events):
                raise ValueError('Cannot combine controller events and non-controller events')
            return True
        return False

    @staticmethod
    def _make_on_walkoff_event_docstring(event):
        args_string = 'Args:\n'
        is_controller = event.event_type == EventType.controller
        if not is_controller:
            args_string = ('{}'
                '\tsender_uids (list[str], optional): The UIDs of the sender which will cause this callback to trigger.\n'
                '\tnames (list[str], optional): The names of the sender to will cause this callback to trigger. Note that unlike '
                'UIDS, these are not guaranteed to be unique.\n'.format(args_string))
        args_string = ('{}\tweak (boolean, optional): Should the callback persist even if function leaves scope? Warning! '
                       'Could cause memory leaks'.format(args_string))
        return '''

Creates a callback for the {0} WalkoffEvent. Requires that the function being decorated have the signature `{1}`.

{2}
'''.format(event.signal_name,
           'def handler(data)' if not is_controller else 'def handler()', args_string)


dispatcher = InterfaceEventDispatcher()


@dispatcher.on_workflow_shutdown(sender_uids='6645b2d61a514cbd8c8ce1094fa63be1')
def x(data):
    print('INHEREHRHERHEHEHRHRHEHEHREHREHEHREHEHREHREHRHHEHRE')
    print('CALLED')
    print(data)



# class TestDispatch(object):
#     def __init__(self):
#         self.funcs = WeakSet()
#
#     def register(self, func):
#         self.funcs.add(func)
#
#     def dispatch(self, sender, **kwargs):
#         print('dispatching to {}'.format(list(self.funcs)))
#         for func in self.funcs:
#             func(sender, **kwargs)
#
# class TestIt(object):
#     router = TestDispatch()
#
#     # @classmethod
#     # def test(cls, sender, **kwargs):
#     #     print('CALLED!!!!!')
#     #     print(sender)
#     #
#     def __new__(cls, *args, **kwargs):
#         xx = cls.dispatch()
#         from functools import partial
#         yy = partial(xx, cls=cls)
#         WalkoffEvent.WorkflowShutdown.connect(yy, weak=False)
#         return super(TestIt, cls).__new__(cls)
#
#     @classmethod
#     def print_it(cls):
#         print('in here')
#
#     @classmethod
#     def dispatch(cls):
#         def test(sender, **kwargs):
#             print('dispatching')
#             cls.router.dispatch(sender, **kwargs)
#         return test
#
#     @classmethod
#     def register(cls, arg):
#         print(arg)
#         def wrapper(func):
#             cls.router.register(func)
#             return func
#         return wrapper
#
# testdisp = TestIt()
# #
# @testdisp.register(1)
# def xxx(sender, **kwargs):
#     print('CALLING INSIDE')