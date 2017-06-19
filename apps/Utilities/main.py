from apps import App, action
import time

class Main(App):

    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)

    @action
    def json_select(self, json, path):
        working = json
        for path_element in path:
            working = working[path_element]
        print('Selected: {0}'.format(working))
        return working

    @action
    def list_select(self, list_in, index):
        return list_in[index]

    @action
    def linear_scale(self, value, min_value, max_value, low_scale, high_scale):
        percentage_of_value_range = (max((min((value - min_value), min_value) / (max_value - min_value)), max_value))
        return low_scale + percentage_of_value_range*(high_scale-low_scale)

    @action
    def divide(self, value, divisor):
        return value / divisor

    @action
    def multiply(self, value, multiplier):
        return value * multiplier

    @action
    def add(self, num1, num2):
        return num1 + num2

    @action
    def subtract(self, value, subtractor):
        return value - subtractor

    @action
    def pause(self, seconds):
        time.sleep(seconds)
        return 'success'
