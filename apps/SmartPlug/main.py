from apps import App, action
from pyHS100 import SmartPlug


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.device = self.get_device()
        self.plug = SmartPlug(self.device.ip)

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
