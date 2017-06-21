import pyowm
from apps import App, action


class Weather(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        self.owm = pyowm.OWM(self.get_device().get_password())

    @action
    def get_current_weather(self, city):
        observation = self.owm.weather_at_place('{0}, us'.format(city))
        return observation.get_weather().to_JSON()

    @action
    def get_current_temperature(self, city):
        observation = self.owm.weather_at_place('{0}, us'.format(city))
        print(observation)
        weather = observation.get_weather()
        print(weather)
        print(weather.get_temperature('fahrenheit')['temp'])
        return weather.get_temperature('fahrenheit')['temp']
