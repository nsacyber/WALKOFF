import socket
import asyncio
import time
import random
import json
import requests

from walkoff_app_sdk.app_base import AppBase


class Basics(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console logging set up behind the scenes.
    """
    __version__ = "1.0.0"
    app_name = "basics"  # this needs to match "name" in api.yaml

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)

    async def hello_world(self):
        """
        Returns Hello World from the hostname the action is run on
        :return: Hello World from your hostname
        """
        message = "This message has been changed by the scavenger!" 

        # This logs to the docker logs
        self.logger.info(message)

        # This sends a log message to the frontend workflow editor
        await self.console_logger.info(message)

        return message

    async def string_to_json(self, call):
        this = json.loads(call)
        return this

    async def echo_string(self, call):
        return f"ECHOING: {call}"

    async def return_plus_one(self, number):
        return number + 1

    async def pause(self, seconds):
        time.sleep(seconds)
        return seconds

    async def random_number(self):
        return random.random()

    async def echo_array(self, data):
        self.logger.info(f"Echoing array: {data}")
        await self.console_logger.info(f"Echoing array: {data}")
        return data

    async def echo_json(self, data):
        self.logger.info(f"Echoing JSON: {data}")
        await self.console_logger.info(f"Echoing JSON: {data}")
        return data

    async def sample_report_data(self):
        message = f"Alpha,Beta,Charlie\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6"
        self.logger.info(message)
        await self.console_logger.info(message)
        return message
      
    @staticmethod
    def _pretty_print(some_dict):
        pretty = json.dumps(some_dict, sort_keys=False, indent=4)
        return pretty
 
    async def ip_lookup(self, ip, apikey):
        url = 'https://www.virustotal.com/vtapi/v2/ip-address/report'
        parameters = {'ip': ip, 'apikey': apikey}
        response = requests.get(url, params=parameters)
        response_dict = response.json()
        pretty = self._pretty_print(response_dict)
        await self.console_logger.info(pretty)

    async def test(self):
        print("test")
        return "foo"

if __name__ == "__main__":
    asyncio.run(Basics.run())
