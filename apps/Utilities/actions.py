from apps import action, event
import time
import json
import csv
import sys
from random import SystemRandom
from apps.Utilities.events import wait


@action
def system_rand():
    return SystemRandom().random()


@action
def round_to_n(number, places):
    return round(number, places)


@action
def echo_object(data):
    return data


@action
def json_select(json_reference, element):
    return json.loads(json_reference)[element]


@action
def list_select(list_reference, index):
    return json.loads(list_reference)[index]


@action
def linear_scale(value, min_value, max_value, low_scale, high_scale):
    fraction_of_value_range = (min((min((value - min_value), min_value) / (max_value - min_value)), 1.0))
    return low_scale + fraction_of_value_range * (high_scale - low_scale)


@action
def divide(value, divisor):
    return value / divisor


@action
def multiply(value, multiplier):
    return value * multiplier


@action
def add(num1, num2):
    return num1 + num2


@action
def subtract(value, subtractor):
    return value - subtractor


@action
def pause(seconds):
    time.sleep(seconds)
    return 'success'


@action
def write_ips_to_csv(ips_reference, path):
    ips = json.loads(ips_reference)

    if sys.version_info[0] == 2:
        with open(path, 'wb') as csvfile:
            fieldnames = ['Host', 'Up']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            for ip in ips:
                if ips[ip] == "up":
                    writer.writerow({'Host': ip, 'Up': 'X'})
                else:
                    writer.writerow({'Host': ip})
    else:
        with open(path, 'w', newline='') as csvfile:
            fieldnames = ['Host', 'Up']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            for ip in ips:
                if ips[ip] == "up":
                    writer.writerow({'Host': ip, 'Up': 'X'})
                else:
                    writer.writerow({'Host': ip})


@event(wait)
def wait_for_event(data):
    return 'success'
