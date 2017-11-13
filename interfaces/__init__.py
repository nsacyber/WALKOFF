from functools import wraps
from core.case.callbacks import WorkflowExecutionStart, WorkflowShutdown
import logging

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


class InterfaceEventDispatch(object):

    callback_lookup = {'Workflow Started': WorkflowExecutionStart, 'Workflow Shutdown': WorkflowShutdown}
    __instance = None  # to make this class a singleton

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(InterfaceEventDispatch, cls).__new__(cls)
        return cls.__instance

    def _make_dispatch_method(self, callback_name):
        def dispatch_method(self, sender, **kwargs):
            if sender.uid in self._router and callback_name in self._router[sender.uid]:
                for func in self._router[sender.uid][callback_name]:
                    func(sender, **kwargs)
        return dispatch_method

    def _make_dispatch_callback(self, dispatch_method_name):
        def callback(sender, **kwargs):
            getattr(self, dispatch_method_name)(self, sender, **kwargs)
        return callback

    def _make_register_method(self, callback_name):
        def on_workflow_started(self, sender_uid):
            def handler(func):
                if sender_uid not in self._router:
                    self._router[sender_uid] = {}
                if callback_name not in self._router[sender_uid]:
                    self._router[sender_uid][callback_name] = [func]
                elif func not in self._router[sender_uid][callback_name]:
                    self._router[sender_uid][callback_name].append(func)
            return handler
        return on_workflow_started

    def __init__(self):
        self._router = {}  # {uid: {'event': [funcs]}}
        for callback_name, callback in self.callback_lookup.items():
            dispatch_method = self._make_dispatch_method(callback_name)
            register_method = self._make_register_method(callback_name)

            callback_name = callback_name.replace(' ', '_')
            dispatch_method_name = '_dispatch_{}_event'.format(callback_name)
            register_method_name = 'on_{}'.format(callback_name)

            setattr(self, dispatch_method_name, dispatch_method)
            setattr(self, register_method_name, register_method)

            callback_function = self._make_dispatch_callback(dispatch_method_name)
            callback.connect(callback_function)


dispatcher = InterfaceEventDispatch()

