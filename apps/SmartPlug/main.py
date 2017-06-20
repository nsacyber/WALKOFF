from apps import App, action
from pyHS100 import SmartPlug
import logging
try:
    import win_inet_pton
except ImportError:
    import os
    if os.name == 'nt':
        logging.getLogger(__name__).error('SmartPlug requires the win_inet_pton package to run on Windows. '
                                          'You can install using pip with "pip install win_inet_pton"')


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.plug = SmartPlug(self.get_device().ip)

    @action
    def get_state(self):
        return self.plug.state

    @action
    def turn_on(self):
        self.plug.turn_on()

    @action
    def turn_off(self):
        self.plug.turn_off()

    @action
    def on_since(self):
        return self.plug.on_since

    def shutdown(self):
        print("SmartPlug Shutting Down")
        return
