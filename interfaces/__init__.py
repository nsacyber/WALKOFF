from functools import wraps
from core.case.callbacks import WorkflowExecutionStart, WorkflowShutdown, StepStarted
import logging

_logger = logging.getLogger(__name__)


class AppWidgetBlueprint(object):
    '''
    Class to create blueprints for custom server endpoints in apps
    '''
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

    _callback_lookup = {'Workflow Started': WorkflowExecutionStart, 'Workflow Shutdown': WorkflowShutdown,
                        'Step Started': StepStarted}
    __step_callback_names = ('Function Execution Success', 'Step Started', 'Input Invalid', 'Step Execution Success',
                             'Step Execution Error', 'Trigger Step Awaiting Data', 'Trigger Step Taken',
                             'Trigger Step Not Taken')
    __instance = None  # to make this class a singleton
    

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(InterfaceEventDispatch, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        self._router = {}  # {uid: {'event': [funcs]}}
        self._app_action_router = {} #{appname: {'action': {'event': [func]}}}
        for callback_name, callback in self._callback_lookup.items():
            dispatch_method = self._make_dispatch_method(callback_name)
            register_method = self._make_register_method(callback_name)

            callback_name = callback_name.replace(' ', '_')
            callback_name = callback_name.lower()
            dispatch_method_name = '_dispatch_{}_event'.format(callback_name)
            register_method_name = 'on_{}'.format(callback_name)
            callback_name = '__{}_callback'
            setattr(self, dispatch_method_name, dispatch_method)
            setattr(self, register_method_name, register_method)

            callback_function = self._make_dispatch_callback(dispatch_method_name)
            print(callback_function)
            setattr(self, callback_name, callback_function)
            callback.connect(callback_function)

    def on_app_actions(self, app, actions='all', callbacks='all'):
        actions = self.__step_callback_names if actions == 'all' else actions
        def handler(func):
            if app not in self._router:
                self._app_action_router[app] = {}
                for action in actions:
                    self._app_action_router[app][action] = [func]
            else:
                pass
            if actions == 'all':
                self._app_action_router[app] = 'all'
            else:
                for action in actions:
                    pass
        return handler


    def _make_dispatch_method(self, callback_name):
        def dispatch_method(self, sender, **kwargs):
            callbacks = self.__get_callbacks(sender, callback_name)
            for func in callbacks:
                print('calling: {}'.format(func))
                func(sender, **kwargs)

        return dispatch_method

    def _make_dispatch_callback(self, dispatch_method_name):
        def callback(sender, **kwargs):
            getattr(self, dispatch_method_name)(self, sender, **kwargs)
        return callback

    def _make_register_method(self, callback_name):
        def on_workflow_event(sender_uid=None, name=None):
            if sender_uid is None and name is None:
                raise ValueError('Either sender_uid or name must specified')

            def handler(func):
                entry_id = sender_uid if sender_uid is not None else name
                if sender_uid not in self._router:
                    self._router[entry_id] = {}
                if callback_name not in self._router[entry_id]:
                    self._router[entry_id][callback_name] = [func]
                elif func not in self._router[entry_id][callback_name]:
                    self._router[entry_id][callback_name].append(func)
            return handler
        return on_workflow_event

    def __get_callbacks(self, sender, callback_name):
        if sender.uid in self._router and callback_name in self._router[sender.uid]:
            return self._router[sender.uid][callback_name]
        elif hasattr(sender, 'name') and sender.name in self._router and callback_name in self._router[sender.name]:
            return self._router[sender.name][callback_name]
        else:
            return []



dispatcher = InterfaceEventDispatch()
print(WorkflowExecutionStart.receivers)

@dispatcher.on_workflow_shutdown('6645b2d61a514cbd8c8ce1094fa63be1')
def x(sender, **kwargs):
    print('CALLED')
    print(kwargs)