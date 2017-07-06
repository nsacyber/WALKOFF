import time
from tests.apps import App, action, event
from tests.apps.HelloWorld.exceptions import CustomException
from tests.apps.HelloWorld.events import event1


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.introMessage = {"message": "HELLO WORLD"}

    @action
    def helloWorld(self):
        return self.introMessage

    @action
    def repeatBackToMe(self, call):
        return "REPEATING: " + call

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

    @action
    def json_sample(self, json_in):
        return (json_in['a'] + json_in['b']['a'] + json_in['b']['b'] + sum(json_in['c']) +
                sum([x['b'] for x in json_in['d']]))

    @event(event1)
    def sample_event(self, data, arg1):
        return data + arg1

    def shutdown(self):
        return
