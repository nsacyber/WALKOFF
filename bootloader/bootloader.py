import logging
import os


import aiodocker
import aioredis

logging.basicConfig(level=logging.info, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("BOOTLOADER")

CONTAINER_ID = os.getenv("HOSTNAME")


class Bootloader:
    def __init__(self, docker_client=None):
        self.docker_client: aiodocker.Docker = docker_client

    @classmethod
    async def init(cls, docker_client):
        self = cls(docker_client)


