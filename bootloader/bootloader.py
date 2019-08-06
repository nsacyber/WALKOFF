import logging
import asyncio
import pathlib
import argparse
import copy
import sys
import os
import re
import shutil
import base64
from minio import Minio
from pathlib import Path

import aiodocker
import aiohttp
import yaml
import yaml.scanner
from tenacity import retry, stop_after_attempt, wait_exponential

from common.config import config, static
from common.docker_helpers import (create_secret, get_secret, delete_secret, get_network, connect_to_aiodocker,
                                   docker_context, stream_docker_log, logger as docker_logger, disconnect_from_network)

logging.basicConfig(level=logging.DEBUG, format="{asctime} - {name} - {levelname}:{message}", style='{')

logger = logging.getLogger("BOOTLOADER")
static.set_local_hostname("local_bootloader")

COMPOSE_BASE = {"version": "3.5",
                "services": {},
                "networks": {"walkoff_default": {"driver": "overlay", "name": "walkoff_default", "attachable": True}},
                "secrets": {"encryption_key": {"external": True}}}

APP_NAME_PREFIX = "walkoff_"

DOCKER_HOST_IP = os.getenv("DOCKER_HOST_IP")
p = Path('./apps').glob('**/*')


def bannerize(text, fill='='):
    columns = shutil.get_terminal_size().columns
    border = "".center(columns, fill)
    banner = f" {text} ".center(columns, fill)
    print(f"\n\n{border}\n{banner}\n{border}\n")


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
    build = {"build": {"context": str(path), "dockerfile": "Dockerfile"}}
    image = {"image": f"{config.DOCKER_REGISTRY}/{APP_NAME_PREFIX}{name}:{path.name}"}
    networks = {"networks": ["walkoff_default"]}
    deploy = {"deploy": {"mode": "replicated", "replicas": 0, "restart_policy": {"condition": "none"}}}
    config_mount = {"configs": ["common_env.yml"]}
    secret_mount = {"secrets": ["walkoff_encryption_key"]}
    shared_path = os.getcwd() + "/data/shared"
    final_mount = shared_path + ":/app/shared"
    volumes_mount = {"volumes": [final_mount]}
    compose["services"] = {name: {**build, **image, ** networks, **deploy, **config_mount,
                                  **secret_mount, **volumes_mount, **env_file}}
    return compose


async def log_proc_output(proc, silent=False):
    stdout, stderr = await proc.communicate()
    if not silent:
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
    for app in pathlib.Path(config.APPS_PATH).iterdir():
        #  grabs only directories and ignores all __* directories i.e. __pycache__
        if app.is_dir() and not re.fullmatch(r"(__.*)", app.name):
            for version in app.iterdir():
                # grabs all valid version directories of form "v0.12.3.45..."
                if re.fullmatch(r"((\d\.?)+)", version.name):
                    composes.append(compose_from_app(version, f"app_{app.name}"))
                logger.info(f"Generated compose for {app.name} version: {version.name}")
    return composes


async def create_encryption_key(docker_client):
    try:
        await get_secret(docker_client, "walkoff_encryption_key")
    except aiodocker.exceptions.DockerError:
        logger.info("Creating secret walkoff_encryption_key...")
        await create_secret(docker_client, "walkoff_encryption_key", base64.urlsafe_b64encode(os.urandom(32)))
    else:
        logger.info("Skipping secret walkoff_encryption_key creation, it already exists.")


async def delete_encryption_key(docker_client):
    try:
        await delete_secret(docker_client, "walkoff_encryption_key")
    except aiodocker.exceptions.DockerError:
        logger.info("Skipping secret walkoff_encryption_key deletion, it doesn't exist.")


async def check_for_network(docker_client):
    try:
        await get_network(docker_client, "walkoff_default")
        return True
    except aiodocker.exceptions.DockerError:
        return False


async def delete_dir_contents(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


@retry(stop=stop_after_attempt(10), wait=wait_exponential(min=1, max=10))
async def deploy_compose(compose):

    try:
        if not isinstance(compose, dict):
            compose = parse_yaml(compose)

        # Dump the compose to a temporary compose file and launch that. This is so we can amend the compose and update the
        # the stack without launching a new one
        dump_yaml(config.TMP_COMPOSE, compose)
        compose = config.TMP_COMPOSE

        proc = await asyncio.create_subprocess_exec("docker", "stack", "deploy", "--compose-file", compose, "walkoff",
                                                    stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
        await log_proc_output(proc)

        if proc.returncode:
            raise OSError
        else:
            return True

    except Exception as e:
        logger.info("Failed deploying, waiting to try again...")
        raise e


async def build_image(docker_client, repo, dockerfile, context_dir, dockerignore):

    logger.info(f"Building {repo} with {dockerfile} in {context_dir}")

    with docker_context(Path(context_dir), dockerignore=dockerignore) as context:
        log_stream = await docker_client.images.build(fileobj=context, tag=repo, rm=True,
                                                      forcerm=True, pull=True, stream=True,
                                                      path_dockerfile=dockerfile,
                                                      encoding="application/x-tar")

    await stream_docker_log(log_stream)


async def push_image(docker_client, repo):

    logger.info(f"Pushing image {repo}.")

    try:
        await docker_client.images.push(repo)
        # await stream_docker_log(log_stream)
        logger.info(f"Pushed image {repo}.")
        return True
    except aiodocker.exceptions.DockerError as e:
        logger.exception(f"Failed to push image: {e}")
        return False


class Bootloader:
    """ A class to hold the logic for each of the possible commands. This follows the dispatch pattern we us in app_base
        for calling actions in apps. The pattern as applied to the CLI follows close to this example:
        https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html#
    """

    def __init__(self, session=None, docker_client=None):
        self.session: aiohttp.ClientSession = session
        self.docker_client: aiodocker.Docker = docker_client
        with open(".dockerignore") as f:
            self.dockerignore = [line.strip() for line in f.readlines()]

    @staticmethod
    async def run():
        """ Landing pad to launch primary command and do whatever async init the bootloader needs. """
        # TODO: fill in the helps, and further develop cli with the end user in mind
        commands = {"up", "build", "down"}
        parser = argparse.ArgumentParser()
        parser.add_argument("command", choices=commands)
        parser.add_argument("args", nargs=argparse.REMAINDER)

        logger.setLevel("DEBUG")
        docker_logger.setLevel("DEBUG")

        # Parse out the command
        args = parser.parse_args(sys.argv[1:2])

        async with aiohttp.ClientSession() as session, connect_to_aiodocker() as docker_client:
            bootloader = Bootloader(session, docker_client)

            if hasattr(bootloader, args.command):
                await getattr(bootloader, args.command)()
            else:
                logger.error("Invalid command.")
                # TODO: Pipe this through the logger. print_help() accepts a file kwarg that we can use to do this
                parser.print_help()

    @retry(stop=stop_after_attempt(10), wait=wait_exponential(min=1, max=10))
    async def wait_for_registry(self):
        try:
            async with self.session.get("http://" + DOCKER_HOST_IP) as resp:
                if resp.status == 200:
                    return True
                else:
                    raise ConnectionError
        except Exception as e:
            logger.info("Registry not available yet, waiting to try again...")
            raise e

    @retry(stop=stop_after_attempt(10), wait=wait_exponential(min=1, max=10))
    async def wait_for_minio(self):
        try:
            async with self.session.get(f"http://{config.MINIO}/minio/health/ready") as resp:
                if resp.status == 200:
                    return True
                else:
                    raise ConnectionError
        except Exception as e:
            logger.info("Minio not available yet, waiting to try again...")
            raise e

    async def push_to_minio(self):
        minio_client = Minio(config.MINIO, access_key='walkoff', secret_key='walkoff123', secure=False)
        flag = False
        try:
            buckets = minio_client.list_buckets()
            for bucket in buckets:
                if bucket.name == "apps-bucket":
                    flag = True
        except:
            logger.info("Bucket doesn't exist.")

        if flag is False:
            minio_client.make_bucket("apps-bucket", location="us-east-1")

        files = [x for x in p if x.is_file()]
        for file in files:
            path_to_file = str(file)
            with open(path_to_file, "rb") as file_data:
                file_stat = os.stat(path_to_file)
                minio_client.put_object("apps-bucket", path_to_file, file_data, file_stat.st_size)

    async def up(self):

        # Create Walkoff encryption key
        return_code = await create_encryption_key(self.docker_client)
        if return_code:
            logger.exception("Could not create secret walkoff_encryption_key. Exiting.")
            os._exit(return_code)

        # Set up a subcommand parser
        parser = argparse.ArgumentParser(description="Bring the WALKOFF stack up and initialize it")
        parser.add_argument("-b", "--build", action="store_true",
                            help="Builds and pushes all WALKOFF components to local registry.")
        parser.add_argument("-d", "--debug", action="store_true",
                            help="Set log level to debug.")

        # Parse out the command
        args = parser.parse_args(sys.argv[2:])

        if args.debug:
            logger.setLevel("DEBUG")
            docker_logger.setLevel("DEBUG")

        logger.info("Creating persistent directories for registry, postgres, portainer...")
        os.makedirs(Path("data") / "registry" / "reg_data", exist_ok=True)
        os.makedirs(Path("data") / "postgres" / "pg_data", exist_ok=True)
        os.makedirs(Path("data") / "portainer" / "prt_data", exist_ok=True)
        os.makedirs(Path("data") / "minio" / "min_data", exist_ok=True)

        # Bring up the base compose with the registry
        logger.info("Deploying base services (registry, postgres, portainer, redis)...")
        base_compose = parse_yaml(config.BASE_COMPOSE)

        await deploy_compose(base_compose)

        await self.wait_for_registry()

        # Merge the base, walkoff, and app composes
        app_composes = generate_app_composes()
        walkoff_compose = parse_yaml(config.WALKOFF_COMPOSE)
        merged_compose = merge_composes(walkoff_compose, app_composes)

        dump_yaml(config.TMP_COMPOSE, merged_compose)

        if args.build:
            walkoff_app_sdk = walkoff_compose["services"]["app_sdk"]
            await build_image(self.docker_client, walkoff_app_sdk["image"],
                              walkoff_app_sdk["build"]["dockerfile"],
                              walkoff_app_sdk["build"]["context"],
                              self.dockerignore)
            await push_image(self.docker_client, walkoff_app_sdk["image"])

            for service_name, service in walkoff_compose["services"].items():
                if "build" in service:
                    await build_image(self.docker_client, service["image"],
                                      service["build"]["dockerfile"],
                                      service["build"]["context"],
                                      self.dockerignore)
                    await push_image(self.docker_client, service["image"])

        await self.wait_for_minio()
        await self.push_to_minio()

        logger.info("Deploying Walkoff stack...")

        return_code = await deploy_compose(merged_compose)

        return return_code

    async def down(self):

        # Set up a subcommand parser
        parser = argparse.ArgumentParser(description="Remove the WALKOFF stack and optionally related artifacts.")
        parser.add_argument("-k", "--key", action="store_true",
                            help="Removes the walkoff_encryption_key secret.")
        parser.add_argument("-r", "--registry", action="store_true",
                            help="Clears the registry bind mount directory.")
        parser.add_argument("-s", "--skipnetwork", action="store_true",
                            help="Skip network removal check. Use this if you have attached external services to it.")
        parser.add_argument("-d", "--debug", action="store_true",
                            help="Set log level to debug.")
        parser.add_argument("-n")

        # Parse out the command
        args = parser.parse_args(sys.argv[2:])

        if args.debug:
            logger.setLevel("DEBUG")
            docker_logger.setLevel("DEBUG")

        logger.info("Removing Walkoff stack and related artifacts...")

        proc = await asyncio.create_subprocess_exec("docker", "stack", "rm", "walkoff", stderr=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.PIPE)

        await log_proc_output(proc)

        # if not args.skipnetwork:
        #     logger.info("Waiting for containers to exit and network to be removed...")
        #     await exponential_wait(check_for_network, [self.docker_client], "Network walkoff_default still exists")

        if args.key:
            resp = input("Deleting encryption key will render database unreadable, and therefore it will be cleared. "
                         "This will delete all workflows, execution results, globals, users, roles, etc. "
                         "Are you sure? (yes/no): ")
            while resp.lower() not in ("yes", "no"):
                resp = input("Please answer 'yes' or 'no': ")

            if resp.lower() == "yes":
                await delete_encryption_key(self.docker_client)
                await delete_dir_contents("data/postgres")

        if args.registry:
            await delete_dir_contents("data/registry")
            await delete_dir_contents("data/minio/min_data")

        return proc.returncode


if __name__ == "__main__":
    asyncio.run(Bootloader.run())
