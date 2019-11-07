import socket
import asyncio
import time
import random
import json

from walkoff_app_sdk.app_base import AppBase


class Basics(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console logging set up behind the scenes.
    """
    __version__ = "1.0.0"
    app_name = "basics"  # this needs to match "name" in api.yaml

    def __init__(self, redis, logger):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        """
        super().__init__(redis, logger)

    async def hello_world(self):
        """
        Returns Hello World from the hostname the action is run on
        :return: Hello World from your hostname
        """
        message = f"Hello World from {socket.gethostname()} in workflow {self.current_execution_id}!"

        # This logs to both the container's stdout and to the UI console in the workflow editor
        self.logger.info(message)

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
        return data

    async def echo_json(self, data):
        self.logger.info(f"Echoing JSON: {data}")
        return data

    async def sample_report_data(self):
        message = f"Alpha,Beta,Charlie\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6\n1,2,3\n4,5,6"
        self.logger.info(message)
        return message


if __name__ == "__main__":
    asyncio.run(Basics.run())
