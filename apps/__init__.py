from server.appdevice import App as _App
from six import add_metaclass
import logging
import importlib
from core.helpers import action  # Change namespace of action

_logger = logging.getLogger(__name__)


class InvalidAppStructure(Exception):
    pass


class UnknownApp(Exception):
    def __init__(self, app):
        super(UnknownApp, self).__init__('Unknown app {0}'.format(app))
        self.app = app


class UnknownAppAction(Exception):
    def __init__(self, app, action):
        super(UnknownAppAction, self).__init__('Unknown action {0} for app {1}'.format(action, app))
        self.app = app
        self.action = action


class AppRegistry(type):
    """
    Metaclass which registers metadata about all the apps
    Assumes apps are in module with <dir>.<app_name> structure
    """
    def __init__(cls, name, bases, nmspc):
        super(AppRegistry, cls).__init__(name, bases, nmspc)
        if not hasattr(cls, 'registry'):
            cls.registry = dict()
        app_name = cls.__get_app_name()
        if app_name is not None:
            cls.registry[app_name] = {'main': cls,
                                      'display': cls.__get_display_function(),
                                      'actions': cls.__get_actions(nmspc)}
        print(cls.registry)

    def __get_app_name(cls):
        try:
            return cls.__module__.split('.')[1]
        except IndexError:
            return None
            # _logger.fatal('Unknown app directory structure. Structure should be <top-level>.<app_name>')
            # raise InvalidAppStructure('Unknown app directory structure. Structure should be <top-level>.<app_name>')

    def __get_display_function(cls):
        try:
            module_name = cls.__module__.rsplit('.', 1)[0]
            display_module = importlib.import_module('{0}.display'.format(module_name))
        except ImportError:
            _logger.warning('App {0} has no module "display"'.format(cls.__get_app_name()))
            return None
        else:
            try:
                load_function = getattr(display_module, 'load')
            except AttributeError:
                _logger.warning('App {0}.display has no property called "load"'.format(cls.__get_app_name()))
                return None
            else:
                if callable(load_function):
                    return load_function
                else:
                    _logger.warning('App {0}.display.load is not callable'.format(cls.__get_app_name()))
                    return None

    @staticmethod
    def __get_actions(nmspc):
        actions = {}
        for property_name, property_value in nmspc.items():
            if callable(property_value) and getattr(property_value, 'action', False):
                actions[property_name] = property_value
        return actions


@add_metaclass(AppRegistry)
class App(object):
    def __init__(self, app, device):
        self.app = app
        self.device = device

    def get_all_devices(self):
        """ Gets all the devices associated with this app """
        return _App.get_all_devices_for_app(self.app)

    def get_device(self):
        """ Gets the device associated with this app """
        return _App.get_device(self.app, self.device)

    def shutdown(self):
        """ When implemented, this menthod performs shutdown procedures for the app """
        pass


def get_app_action(app_name, action_name):
    try:
        app = App.registery[app_name]
    except KeyError:
        raise UnknownApp(app_name)
    else:
        try:
            return app['actions'][action_name]
        except:
            raise UnknownAppAction(app_name, action_name)


def get_all_actions_for_app(app_name):
    try:
        return App.registery[app_name]['actions']
    except KeyError:
        raise UnknownApp(app_name)


def get_app(app_name):
    try:
        return App.registery[app_name]['main']
    except KeyError:
        raise UnknownApp(app_name)


def get_app_display(app_name):
    try:
        return App.registery[app_name]['main']
    except KeyError:
        raise UnknownApp(app_name)
