import logging
from apps import App, action
import requests
import json

logger = logging.getLogger(__name__)
import time


class Main(App):
    """
       Skeleton example app to build other apps off of
    
       Args:
           name (str): Name of the app
           device (list[str]): List of associated device names
           
    """

    def __init__(self, name=None, device=None):
        print('initializing')
        App.__init__(self, name, device)  # Required to call superconstructor
        self.headers = {"Authorization": "Bearer {0}".format(self.get_device().get_password())}
        self.name = self.get_device().username

        self.base_url = 'https://api.lifx.com/v1/lights'
        print('initialized')

    def __api_url(self, endpoint, act_on_all=False):
        if act_on_all:
            return '{0}/all/{2}'
        else:
            return '{0}/label:{1}/{2}'.format(self.base_url, self.name, endpoint)

    @action
    def list_lights(self):
        response = requests.get(self.__api_url('', act_on_all=True), headers=self.headers)
        return response.text

    @action
    def set_state(self, power, color, brightness, duration, infrared):
        """
        Sets the state of the light
        power: on or off
        color: color to set the lights to
        brightness: int from 0 to 1
        duration: seconds for the action to last
        infrared: 0 to 1. maximum brightness of infrared channel
        """
        payload = {"duration": duration}
        if power is not None:
            payload['power'] = power
        if color is not None:
            payload['color'] = color
        if brightness is not None:
            payload['brightness'] = brightness
        if infrared is not None:
            payload['duration'] = duration
        response = requests.put(self.__api_url('state'.format(self.name)), data=payload, headers=self.headers)
        time.sleep(duration)
        return json.loads(response.text)

    @action
    def toggle_power(self, duration, wait):
        """
        Sets the state of the light
        duration: seconds for the action to last
        """
        payload = {"duration": duration}
        response = requests.post(self.__api_url('toggle'.format(self.name)), data=payload, headers=self.headers)
        if wait:
            time.sleep(duration)
        return json.loads(response.text)

    @action
    def breathe_effect(self, color, from_color, period, cycles, persist, power_on, peak, wait):
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
        payload = {"color": color,
                   "period": period,
                   "cycles": cycles,
                   "persist": persist,
                   "power_on": power_on,
                   "peak": peak}
        if from_color is not None:
            payload['from_color'] = from_color
        response = requests.post(self.__api_url('effects/breathe'.format(self.name)),
                                 data=payload,
                                 headers=self.headers)
        if wait:
            time.sleep(period * cycles)
        return json.loads(response.text)

    @action
    def pulse_effect(self, color, from_color, period, cycles, persist, power_on, wait):
        """
        Quickly flashes between two colors
        color: color to use for the breathe effect
        from_color: color to start the breathe effect from
        period: Time in milliseconds between cycles
        cycles: Number of times to repeat the effect
        persist: If false set teh light back to its previous value when effect ends. Else leave at last effect
        power_on: If true, turn on the light if not already on
        """
        payload = {"color": color,
                   "period": period,
                   "cycles": cycles,
                   "persist": persist,
                   "power_on": power_on}
        if from_color is not None:
            payload['from_color'] = from_color
        response = requests.post(self.__api_url('effects/pulse'),
                                 data=payload,
                                 headers=self.headers)
        if wait:
            time.sleep(period * cycles)
        return json.loads(response.text)
