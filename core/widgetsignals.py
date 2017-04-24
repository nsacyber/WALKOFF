from blinker import signal

_widget_signals = {}


__widget_signal_name_separator = '-'


def create_widget_signal_name(app_name, widget_name):
    return '{0}{1}{2}'.format(app_name, __widget_signal_name_separator, widget_name)


def get_widget_signal(app_name, widget_name):
    key = (app_name, widget_name)
    if key not in _widget_signals:
        _widget_signals[key] = signal(create_widget_signal_name(app_name, widget_name))
    return _widget_signals[key]

