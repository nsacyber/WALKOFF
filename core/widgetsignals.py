from blinker import signal

_widget_signals = {}


__widget_signal_name_separator = '-'


def create_widget_signal_name(app_name, widget_name):
    """ Creates a consistent widget signal name
    Args:
        app_name (str): The app name
        widget_name (str): The widget anme
    """
    return '{0}{1}{2}'.format(app_name, __widget_signal_name_separator, widget_name)


def get_widget_signal(app_name, widget_name):
    """ Gets a widget signal for the given app and widget. If none exists, it creates one.
    Args:
        app_name (str): The app name
        widget_name (str): The widget name
    Returns:
         A blinker Signal object used for the app widget
    """
    key = (app_name, widget_name)
    if key not in _widget_signals:
        _widget_signals[key] = signal(create_widget_signal_name(app_name, widget_name))
    return _widget_signals[key]

