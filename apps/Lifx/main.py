import logging
from apps import App
import requests
import json
logger = logging.getLogger(__name__)


class Main(App):
    """
       Skeleton example app to build other apps off of
    
       Args:
           name (str): Name of the app
           device (list[str]): List of associated device names
           
    """
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)   # Required to call superconstructor
        self.headers = {"Authorization": "Bearer {0}".format(self.get_device().get_password())}
        self.name = self.get_device().username
        self.base_url = 'https://api.lifx.com/v1/lights/'

    def __api_url(self, endpoint):
        return '{0}{1}'.format(self.base_url, endpoint)

    def list_lights(self, args):
        response = requests.get(self.__api_url('all'), headers=self.headers)
        return json.dumps(response)

    def set_state_all_lights(self, args={}):
        """
        Sets the state of all connected lights
        power: on or off
        color: color to set the lights to
        brightness: int from 0 to 1000
        duration: seconds for the action to last
        infrared: 0 to 1000. maximum brightness of infrared channel
        :return:
        """
        payload = {"power": args['power'],
                   "color": args['color'],
                   "brightness": args['brightness']/1000.,
                   "duration": args['duration'],
                   "infrared": args['infrared']/1000.}
        response = requests.put(self.__api_url('all/state'), data=payload, headers=self.headers)
        return json.dumps(response)

    def set_state(self, args={}):
        """
        Sets the state of the light
        power: on or off
        color: color to set the lights to
        brightness: int from 0 to 1000
        duration: seconds for the action to last
        infrared: 0 to 1000. maximum brightness of infrared channel
        """
        payload = {"power": args['power'],
                   "color": args['color'],
                   "brightness": args['brightness']/1000.,
                   "duration": args['duration'],
                   "infrared": args['infrared']/1000.}
        response = requests.put(self.__api_url('label:{0}/state'.format(self.name)), data=payload, headers=self.headers)
        return json.dumps(response)

    def toggle_power(self, args={}):
        """
        Sets the state of the light
        duration: seconds for the action to last
        """
        payload = {"duration": args['duration']}
        response = requests.post(self.__api_url('label:{0}/state'.format(self.name)), data=payload, headers=self.headers)
        return json.dumps(response)

    def breathe_effect(self, args={}):
        """
        Slowly fades between two colors
        color: color to use for the breathe effect
        from_color: color to start the breathe effect from
        period: Time in seconds between cycles
        cycles: Number of times to repeat the effect
        persist: If false set teh light back to its previous value when effect ends. Else leave at last effect
        power_on: If true, turn on the light if not already on
        peak: where in the period the target color is at its maximum. Between 0 and 10
        """
        payload = {"color": args['color'],
                   "from_color": args['from_color'],
                   "period": args['period'],
                   "cycles": args['cycles'],
                   "persist": args['persist'],
                   "power_on": args['power_on'],
                   "peak": args['peak']/10.}
        response = requests.put(self.__api_url('label:{0}/effects/breathe'.format(self.name)),
                                data=payload,
                                headers=self.headers)
        return json.dumps(response)

    def pulse_effect(self, args={}):
        """
        Quickly flashes between two colors
        color: color to use for the breathe effect
        from_color: color to start the breathe effect from
        period: Time in seconds between cycles
        cycles: Number of times to repeat the effect
        persist: If false set teh light back to its previous value when effect ends. Else leave at last effect
        power_on: If true, turn on the light if not already on
        """
        payload = {"color": args['color'],
                   "from_color": args['from_color'],
                   "period": args['period'],
                   "cycles": args['cycles'],
                   "persist": args['persist'],
                   "power_on": args['power_on']}
        response = requests.put(self.__api_url('label:{0}/effects/pulse'.format(self.name)),
                                data=payload,
                                headers=self.headers)
        return json.dumps(response)
