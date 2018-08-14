import time

from apps import App, action
from tests.testapps.HelloWorld.exceptions import CustomException


@action
def global1(arg1):
    return arg1


@action
def helloWorld():
    return {"message": "HELLO WORLD"}


@action
def repeatBackToMe(call):
    return "REPEATING: " + call


@action
def returnPlusOne(number):
    return number + 1


@action
def pause(self, seconds):
    time.sleep(seconds)


@action
def addThree(num1, num2, num3):
    return num1 + num2 + num3


@action
def buggy_action():
    raise CustomException


@action
def json_sample(json_in):
    return (json_in['a'] + json_in['b']['a'] + json_in['b']['b'] + sum(json_in['c']) +
            sum([x['b'] for x in json_in['d']]))


@action
def dummy_action(status, other=False):
    if other:
        return

    if status:
        return True, 'Success'
    else:
        return False, 'Failure'


class Main(App):
    def __init__(self, name, device, context):
        App.__init__(self, name, device, context)
        self.introMessage = {"message": "HELLO WORLD"}

    def shutdown(self):
        return
