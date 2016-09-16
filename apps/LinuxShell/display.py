from flask_security import current_user
from flask import request
import requests, json


def get_device_list():
    auth_token = current_user.get_auth_token()
    if auth_token:
        baseURL = request.base_url.replace(request.path, "")
        device_list_req = requests.post(baseURL + "/configuration/LinuxShell/devices/all", headers={"Authentication-Token":auth_token}, verify=False)
        if device_list_req.status_code == 200:
            device_list = device_list_req.json()
            device_list_parsed = []

            if "status" not in device_list:
                for device in device_list:
                    device_list_parsed.append((device['name'],device['ip'],device['port'],device['username']))
            return device_list_parsed
        else:
            return "Could not retrieve devices"
    else:
        return "Current user not logged in"

def load(args={}):
    device_list = get_device_list()
    return {"device_list": device_list}