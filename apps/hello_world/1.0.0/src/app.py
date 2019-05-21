import socket
import asyncio
import time
import random

from walkoff_app_sdk.app_base import AppBase


class HelloWorld(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console logging set up behind the scenes.
    """
    __version__ = "1.0.0"
    app_name = "hello_world"  # this needs to match "name" in api.yaml

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
        message = f"Hello World from {socket.gethostname()} in workflow {self.current_execution_id}!"

        # This logs to the docker logs
        self.logger.info(message)

        # This sends a log message to the frontend workflow editor
        await self.console_logger.info(message)

        return message

    async def repeat_back_to_me(self, call):
        return f"REPEATING: {call}"

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


if __name__ == "__main__":
    asyncio.run(HelloWorld.run(), debug=True)
