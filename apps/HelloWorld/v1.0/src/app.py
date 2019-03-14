import socket
import asyncio
import time

from app_sdk.app_base import AppBase


class HelloWorld(AppBase):
    __version__ = "v1.0"

    def __init__(self, redis, logger, console_logger=None):
        super().__init__(redis, logger, console_logger)
    
    async def hello_world(self):
        self.logger.debug(f"This is a test from {socket.gethostname()}")
        await self.console_logger.info(f"This is a test from {socket.gethostname()}")
        return {f"message": "HELLO WORLD FROM {socket.gethostname()}"}

    async def repeat_back_to_me(self, call):
        return f"REPEATING: {call}"

    async def return_plus_one(self, number):
        return number + 1
    
    async def pause(self, seconds):
        time.sleep(seconds)
        return seconds

    async def echo_array(self, data):
        self.logger.info(f"Echoing array: {data}")
        await self.console_logger.info(f"Echoing array: {data}")
        return data

    async def echo_json(self, data):
        self.logger.info(f"Echoing JSON: {data}")
        await self.console_logger.info(f"Echoing JSON: {data}")
        return data


if __name__ == "__main__":
    asyncio.run(HelloWorld.run())

