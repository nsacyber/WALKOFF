import logging
import time

from apps import App, action

logger = logging.getLogger("apps")

@action
def hello_world():
    logger.debug("This is a test")
    return {"message": "HELLO WORLD"}


@action
def repeat_back_to_me(call):
    return "REPEATING: " + call


@action
def return_plus_one(number):
    return number + 1


@action
def pause(seconds):
    time.sleep(seconds)


class HelloWorld(App):
    """This app defines the same actions as above, but bound to an app instance. This instance will keep track fo how
    many total actions are called for this app's instance.
    """

    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        # Functions and Variables that are designed to exist across functions go here
        self.introMessage = {"message": "HELLO WORLD"}
        self.total_called_functions = 0

    @action
    def hello_world_bound(self):
        self.total_called_functions += 1
        return self.introMessage

    @action
    def repeat_back_to_me_bound(self, call):
        self.total_called_functions += 1
        return "REPEATING: " + call

    @action
    def return_plus_one_bound(self, number):
        self.total_called_functions += 1
        return number + 1

    @action
    def pause_bound(self, seconds):
        self.total_called_functions += 1
        time.sleep(seconds)

    @action
    def total_actions_called(self):
        return self.total_called_functions

    def shutdown(self):
        return