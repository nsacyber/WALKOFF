import socket
import asyncio
import time
import logging

from app_sdk.app_base import AppBase


class HelloWorld(AppBase):
    __version__ = "v1.0"
    def __init__(self, redis=None, logger=None):
        super().__init__(redis, logger)
    
    def hello_world(self):
        logger.debug(f"This is a test from {socket.gethostname()}")
        return {f"message": "HELLO WORLD FROM {socket.gethostname()}"}

    def repeat_back_to_me(self, call):
        return f"REPEATING: {call}"

    def return_plus_one(self, number):
        return number + 1
    
    def pause(self, seconds):
        time.sleep(seconds)
        return seconds
        
        
if __name__ == "__main__":
    import argparse
    LOG_LEVELS = ("debug", "info", "error", "warn", "fatal", "DEBUG", "INFO", "ERROR", "WARN", "FATAL")
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", dest="log_level", choices=LOG_LEVELS, default="DEBUG")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format="{asctime} - {name} - {levelname}:{message}", style='{')
    logger = logging.getLogger("HelloWorld")

    async def run():
        app = HelloWorld(logger=logger)
        async with app.connect_to_redis_pool():
            await app.get_actions()

    asyncio.run(run())

