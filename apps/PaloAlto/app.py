import logging
import requests
from pandevice import firewall
import xml.etree.ElementTree as ET

from apps import App, action

logger = logging.getLogger(__name__)


class PaloAlto(App):
    """
       Palo Alto App
    
       Args:
           name (str): Name of the app
           device (list[int]): List of associated device IDs
           
    """

    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)  # Required to call superconstructor
        self.session = requests.Session()
        self.ip = self.device_fields["ip"] + ":" + str(self.device_fields["port"])

        url = "https://" + self.ip + "/api/?type=keygen&user=" + self.device_fields["username"] + "&password=" + \
              self.device.get_encrypted_field("password")
        response = self.session.get(url, verify=False)
        tree = ET.fromstring(response.text)
        if tree.attrib["status"] == "success":
            self.key_suffix = tree[0][0].text

        self.firewall = firewall.Firewall(self.device_fields["ip"], self.device_fields["username"],
                                          self.device.get_encrypted_field("password"))

    @action
    def execute_operational_command(self, command):
        response = self.firewall.op(command, xml=True)
        return response

    @action
    def commit(self):
        url = "https://" + self.ip + "/api/?type=commit&cmd=<commit></commit>"
        response = self.session.get(url, verify=False)
        return response.text

    @action
    def validate(self):
        url = "https://" + self.ip + "/api/?type=commit&cmd=<commit><validate></validate></commit>"
        response = self.session.get(url, verify=False)
        return response.text

    @action
    def add_ip_to_dynamic_block_list(self, name, ip, description):
        element = '<entry name="' + name + '"><url>' + ip + '</url><description>' + description + \
                  '</description></entry>'

        xpath = "/config/devices/entry/vsys/entry/external-list"
        url = 'https://' + self.ip + '/api/'
        payload = {'type': 'config', 'action': 'set', 'xpath': xpath, 'element': element, 'key': self.key_suffix}

        response = self.session.get(url, params=payload, verify=False)
        return response.text

    @action
    def remove_ip_from_dynamic_block_list(self, name, ip, description):
        element = '<entry name="' + name + '"><url>' + ip + '</url><description>' + description + \
                  '</description></entry>'

        xpath = "/config/devices/entry/vsys/entry/external-list"
        url = 'https://' + self.ip + '/api/'
        payload = {'type': 'config', 'action': 'delete', 'xpath': xpath, 'element': element, 'key': self.key_suffix}

        response = self.session.get(url, params=payload, verify=False)
        return response.text

    @action
    def get_running_config(self):
        url = 'https://' + self.ip + '/api/?type=config&action=show'
        payload = {'key': self.key_suffix}
        response = self.session.get(url, params=payload, verify=False)
        return response.text

    def shutdown(self):
        return
