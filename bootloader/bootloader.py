import logging
import asyncio
import pathlib
import argparse
import copy
import sys
import os
import re

import aioredis
import aiodocker
import aiohttp
import yaml
import yaml.scanner

from common import docker_helpers, helpers, redis_helpers
from common.config import Config

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("BOOTLOADER")

CONTAINER_ID = os.getenv("HOSTNAME", "local_umpire")

COMPOSE_BASE = {"version": "3.5",
                "services": {},
                "networks": {"walkoff_default": {"driver": "overlay", "name": "walkoff_default"}},
                "secrets": {"encryption_key": {"external": True}}}

APP_NAME_PREFIX = "walkoff_app_"


def parse_yaml(path):
    with open(path) as fp:
        try:
            return yaml.safe_load(fp)
        except yaml.YAMLError as e:
            logger.info(f"Invalid yaml: {path}. {e}")
        except yaml.scanner.ScannerError as e:
            logger.info(f"Invalid yaml: {path}. {e}")


def dump_yaml(path, obj):
    with open(path, 'w') as fp:
        try:
            return yaml.dump(obj, fp)
        except yaml.YAMLError as e:
            logger.info(f"Invalid yaml: {path}. {e}")


def parse_env_file(path):
    with open(path) as fp:
        return [line.strip() for line in fp]


def compose_from_app(path: pathlib.Path, name):
    env_txt = path / "env.txt"
    env_file = {}
    if env_txt.exists():
        env_file = {"environment": parse_env_file(env_txt)}
    compose = copy.deepcopy(COMPOSE_BASE)
    build = {"build": {"context": str(path), "dockerfile": str(path / "Dockerfile")}}
    image = {"image": f"{Config.DOCKER_REGISTRY}/{APP_NAME_PREFIX}{name}"}
    deploy = {"deploy": {"mode": "replicated", "replicas": 0, "restart_policy": {"condition": "none"}}}
    restart = {"restart": "no"}
    compose["services"] = {name: {**build, **image, **deploy, **restart, **env_file}}
    return compose


async def log_proc_output(proc):
    stdout, stderr = await proc.communicate()
    if proc.returncode:
        for line in stderr.decode().split('\n'):
            if line != '':
                logger.error(line)
    else:
        for line in stdout.decode().split('\n'):
            if line != '':
                logger.info(line)


def merge_composes(base, others):
    if not isinstance(base, dict):
        base = parse_yaml(base)
        if base.get("services") is None:
            base["services"] = {}
    if not isinstance(others[0], dict):
        others = [parse_yaml(o) for o in others]
    for o in others:
        base["services"].update(o.get("services", {}))
    return base


def generate_app_composes():
    # TODO: Probably find a way to incorporate the app repo in here as well to eliminate mounting files to umpire
    composes = []
    for app in pathlib.Path(Config.APPS_PATH).iterdir():
        #  grabs only directories and ignores all __* directories i.e. __pycache__
        if app.is_dir() and not re.fullmatch(r"(__.*)", app.name):
            for version in app.iterdir():
                # grabs all valid version directories of form "v0.12.3.45..."
                if re.fullmatch(r"((\d\.?)+)", version.name):
                    composes.append(compose_from_app(version, app.name))
                logger.info(f"Generated compose for {app.name} version: {version.name}")
    return composes


async def deploy_compose(compose):
    if not isinstance(compose, dict):
        compose = parse_yaml(compose)

    # Dump the compose to a temporary compose file and launch that. This is so we can amend the compose and update the
    # the stack without launching a new one
    dump_yaml(Config.TMP_COMPOSE, compose)
    compose = Config.TMP_COMPOSE

    proc = await asyncio.create_subprocess_exec("docker", "stack", "deploy", "--compose-file", compose, "walkoff",
                                                stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    await log_proc_output(proc)

    return proc.returncode


async def build_image(repo, dockerfile, context):
    proc = await asyncio.create_subprocess_exec("docker", "build", "-t", repo,
                                                "-f", dockerfile, context,
                                                stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    await log_proc_output(proc)

    return proc.returncode


async def push_image(repo):
    proc = await asyncio.create_subprocess_exec("docker", "push", repo,
                                                stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    await log_proc_output(proc)

    return proc.returncode


class Bootloader:
    """ A class to hold the logic for each of the possible commands. This follows the dispatch pattern we us in app_base
        for calling actions in apps. The pattern as applied to the CLI follows close to this example:
        https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html#
    """
    def __init__(self, session=None):
        self.session: aiohttp.ClientSession = session

    @staticmethod
    async def run():
        """ Landing pad to launch primary command and do whatever async init the bootloader needs. """
        # TODO: fill in the helps, and further develop cli with the end user in mind
        commands = {"up", "build", "down"}
        parser = argparse.ArgumentParser()
        parser.add_argument("command", choices=commands)
        parser.add_argument("args", nargs=argparse.REMAINDER)

        # Parse out the command
        args = parser.parse_args(sys.argv[1:2])

        async with aiohttp.ClientSession() as session:
            bootloader = Bootloader(session)

            if hasattr(bootloader, args.command):
                await getattr(bootloader, args.command)()
            else:
                logger.error("Invalid command.")
                # TODO: Pipe this through the logger. print_help() accepts a file kwarg that we can use to do this
                parser.print_help()

    async def _wait_for_registry(self):
        time = 0.25
        while True:
            try:
                async with self.session.get("http://" + Config.DOCKER_REGISTRY) as resp:
                    if resp.status == 200:
                        return
            except aiohttp.ClientConnectionError:
                logger.info(f"Registry not available yet. Checking again in {time} seconds.")
                await asyncio.sleep(time)
                time *= 2

    async def up(self):
        # Set up a subcommand parser
        parser = argparse.ArgumentParser(description="Bring the WALKOFF stack up and initialize it")
        parser.add_argument("--build", action="store_true")

        # Parse out the command
        args = parser.parse_args(sys.argv[2:])

        # Bring up the base compose with the registry
        base_compose = parse_yaml(Config.BASE_COMPOSE)
        return_code = await deploy_compose(base_compose)
        await self._wait_for_registry()

        # Merge the base, walkoff, and app composes
        app_composes = generate_app_composes()
        walkoff_compose = parse_yaml(Config.WALKOFF_COMPOSE)
        merged_compose = merge_composes(walkoff_compose, app_composes)

        builders = []
        if args.build:
            for service_name, service in merged_compose["services"].items():
                builders.append(build_image(service["image"],
                                service["build"]["dockerfile"], service["build"]["context"]))

        await asyncio.gather(*builders, return_exceptions=True)

        pushers = []
        # The registry is up so lets push the images we need into it
        for service_name, service in merged_compose["services"].items():
            pushers.append(push_image(service["image"]))

        await asyncio.gather(*pushers, return_exceptions=True)

        return_code = await deploy_compose(merged_compose)

        return

    async def down(self):
        proc = await asyncio.create_subprocess_exec("docker", "stack", "rm", "walkoff", stderr=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.PIPE)
        await log_proc_output(proc)

        return


if __name__ == "__main__":
    asyncio.run(Bootloader.run())
