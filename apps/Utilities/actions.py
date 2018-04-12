import csv
import json
import sys
import time
from random import SystemRandom

from apps import action
from apps.messaging import Text, Message, send_message, Url, AcceptDecline


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
def echo_array(data):
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


@action
def send_text_message(subject, message, users=None, roles=None):
    text = Text(message)
    message = Message(subject=subject, body=[text])
    send_message(message, users=users, roles=roles)
    return 'success'


@action
def basic_request_user_approval(users=None, roles=None):
    text = Text('A workflow requires your authentication')
    message = Message(subject='Workflow awaiting approval', body=[text, AcceptDecline()])
    send_message(message, users=users, roles=roles)
    return 'success'


@action
def create_text_message_component(text):
    return Text(text).as_json()


@action
def create_url_message_component(url, title=None):
    return Url(url, title=title).as_json()


@action
def create_accept_decline_message_component():
    return AcceptDecline().as_json()


@action
def create_empty_message(subject=None):
    return Message(subject=subject).as_json()


@action
def append_text_message_component(message, text):
    message = Message.from_json(message)
    message.append(Text(text))
    return message.as_json()


@action
def append_url_message_component(message, url, title=None):
    message = Message.from_json(message)
    message.append(Url(url, title=title))
    return message.as_json()


@action
def append_accept_decline_message_component(message):
    message = Message.from_json(message)
    message.append(AcceptDecline())
    return message.as_json()


@action
def combine_messages(message1, message2):
    message1 = Message.from_json(message1)
    message1 += Message.from_json(message2)
    return message1.as_json()


@action
def set_message_subject(message, subject):
    message = Message.from_json(message)
    message.subject = subject
    return message.as_json()


@action
def send_full_message(message, users=None, roles=None):
    message = Message.from_json(message)
    send_message(message, users=users, roles=roles)
    return 'success'


@action
def accept_decline(action):
    r = action.lower() == 'accept'
    return r, "Accepted" if r else "Declined"


@action
def csv_to_json(path, separator=',', encoding='ascii', headers=None):
    import sys
    if sys.version[0] == '2':
        from io import open
    try:
        with open(path, encoding=encoding) as f:
            results = []
            if not headers:
                headers = f.readline().split(separator)
            for line in f.readlines():
                line = line.strip('\r\n')
                results.append({key: value for key, value in zip(headers, line.split(','))})
        return results
    except (IOError, OSError) as e:
        return e, 'File Error'
