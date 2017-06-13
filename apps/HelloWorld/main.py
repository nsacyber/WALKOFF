import time
import logging
from apps import App, action

logger = logging.getLogger(__name__)


# There is an associated Hello world test workflow which can be executed
class Main(App):
    def __init__(self, name=None, device=None):
        # The parent app constructor looks for a device configuration and returns that as a dict called self.config
        App.__init__(self, name, device)
        # Functions and Variables that are designed to exist across functions go here
        self.introMessage = {"message": "HELLO WORLD"}

    # Every function in Main is an action that can be taken
    # Every function needs to define an args argument which receives a dictionary of input parameters
    @action
    def helloWorld(self):
        return self.introMessage

    # Example using arguments
    # Repeats back the contents of the call argument
    @action
    def repeatBackToMe(self, call):
        return "REPEATING: " + call

    # Increments number by one
    @action
    def returnPlusOne(self, number):
        return number + 1

    @action
    def pause(self, seconds):
        time.sleep(seconds)

    def shutdown(self):
        # print("SHUTTING DOWN")
        return
