import time
from tests.apps import App, action
from tests.apps.HelloWorld.exceptions import CustomException

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
        # LOOK AT YOUR CONSOLE WHEN EXECUTING
        return self.introMessage

    # Example using arguments
    # Repeats back the contents of the call argument
    @action
    def repeatBackToMe(self, call):
        # print("REPEATING: " + args["call"]())
        return "REPEATING: " + call

    # Increments number by one
    @action
    def returnPlusOne(self, number):
        return number + 1

    @action
    def pause(self, seconds):
        time.sleep(seconds)

    @action
    def addThree(self, num1, num2, num3):
        return num1 + num2 + num3

    @action
    def buggy_action(self):
        raise CustomException

    def shutdown(self):
        # print("SHUTTING DOWN")
        return
