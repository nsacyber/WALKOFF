import logging
import os
import re
import json
import copy
import base64
import tarfile
from io import BytesIO
from pathlib import Path
from contextlib import contextmanager, asynccontextmanager

import aiodocker
from aiodocker.utils import clean_map
import docker
from docker.models.services import _get_create_service_kwargs
from docker.types.services import ServiceMode, Resources, EndpointSpec, RestartPolicy

from compose.cli.command import get_project as get_compose_project
from compose.utils import timeparse, parse_bytes
from compose.config.environment import Environment

from common.config import config
from common.helpers import sint, sfloat

logger = logging.getLogger("UMPIRE")


class DockerBuildError(Exception):
    pass


# TODO: Clean a lot of this up and rectify the inconsistencies between the different docker libraries
class ServiceKwargs:
    @classmethod
    def configure(cls, image, service, secrets=None, **kwargs):
        self = ServiceKwargs()
        options = service.options
        deploy_opts = options.get("deploy", {})
        prefs = deploy_opts.get("placement", {}).get("preferences", {})

        # Map compose options to service options
        self.image = image
        self.constraints = deploy_opts.get("placement", {}).get("constraints")
        self.preferences = [kv for pref in prefs for kv in pref.items()]
        self.container_labels = options.get("labels")

        self.endpoint_spec = EndpointSpec(deploy_opts.get("endpoint_mode"),
                                          {p.published: p.target for p in options.get("ports", [])})

        self.env = options.get("environment", None)
        self.hostname = options.get("hostname")
        self.isolation = options.get("isolation")
        self.labels = {k: v for k, v in (kv.split('=') for kv in deploy_opts.get("labels", []))}
        self.log_driver = options.get("logging", {}).get("driver")
        self.log_driver_options = options.get("logging", {}).get("options")
        self.mode = ServiceMode(deploy_opts.get("mode", "replicated"), deploy_opts.get("replicas", 1))
        self.networks = [config["UMPIRE"]["network"]]  # Similar to mounts. I don't see the use case but see the issues

        resource_opts = deploy_opts.get("resources", {})
        if resource_opts:
            # Unpack any generic_resources defined i.e. gpus and such
            reservation_opts = resource_opts.get("reservations", {})
            generic_resources = {}
            for generic_resource in reservation_opts.get("generic_resources", {}):
                discrete_resource_spec = generic_resource["discrete_resource_spec"]
                generic_resources[discrete_resource_spec["kind"]] = discrete_resource_spec["value"]
            cpu_limit = sfloat(resource_opts.get("limits", {}).get("cpus"))
            cpu_reservation = sfloat(reservation_opts.get("cpus"))
            nano_cpu_limit = sint(cpu_limit * 1e9) if cpu_limit is not None else None
            nano_cpu_reservation = sint(cpu_reservation * 1e9) if cpu_reservation is not None else None
            self.resources = Resources(cpu_limit=nano_cpu_limit,
                                       mem_limit=parse_bytes(resource_opts.get("limits", {}).get("memory", '')),
                                       cpu_reservation=nano_cpu_reservation,
                                       mem_reservation=parse_bytes(reservation_opts.get("memory", '')),
                                       generic_resources=generic_resources)

        restart_opts = deploy_opts.get("restart_policy", {})
        if restart_opts:
            # Parse the restart policy
            delay = timeparse(restart_opts.get("delay", "0s"))
            window = timeparse(restart_opts.get("restart_opts", "0s"))
            self.restart_policy = RestartPolicy(condition=restart_opts.get("condition", ),
                                                delay=delay,
                                                max_attempts=sint(restart_opts.get("max_attempts", 0)),
                                                window=window)

        self.secrets = secrets

        # Grab any key word arguments that may have been given
        [setattr(self, k, v) for k, v in kwargs.items() if hasattr(self, k)]

        service_kwargs = _get_create_service_kwargs('create', copy.copy(self.__dict__))

        # This is needed because aiodocker assumes the Env is a dictionary for some reason...
        if self.env is not None:
            service_kwargs["task_template"]["ContainerSpec"]["Env"] = self.env

        return service_kwargs


async def create_secret(client, name, data):
    data = base64.b64encode(data)
    data = data.decode("ascii")
    body = {"Data": data, "Name": name}
    headers = {"Content-Type": "application/json"}
    resp = await client._query("secrets/create", "POST", data=json.dumps(body), headers=headers)
    return resp


async def update_service(client, service_id, version, *, image=None, rollback=None, mode=None):
    if image is None and rollback is False:
        raise ValueError("You need to specify an image.")

    inspect_service = await client.services.inspect(service_id)
    spec = inspect_service["Spec"]

    if mode is not None:
        spec["Mode"] = mode

    if image is not None:
        spec["TaskTemplate"]["ContainerSpec"]["Image"] = image

    params = {"version": version}
    if rollback is True:
        params["rollback"] = "previous"

    data = json.dumps(clean_map(spec))

    await client._query_json(
        "services/{service_id}/update".format(service_id=service_id),
        method="POST",
        data=data,
        params=params,
    )
    return True
    

async def get_secret(client: aiodocker.Docker, secret_id):
    resp = await client._query(f"secrets/{secret_id}")
    return await resp.json()


def normalize_name(name, delimiter=''):
    """ Super arbitrary naming convention for docker images/services... """
    return re.sub(r'[^-_a-z0-9]', delimiter, name.lower())


def get_project(path):
    project = get_compose_project(path, environment=load_docker_env(), project_name=config["UMPIRE"]["app_prefix"])
    project.path = path  # we'll add this in to refresh the project later
    return project


def load_docker_env():
    environment = os.environ
    environment.update({key: val for key, val in config["DOCKER_ENV"].items()})
    return Environment(environment)


def connect_to_docker():
    client = docker.from_env(environment=load_docker_env())
    try:
        if client.ping():
            logger.debug(f"Connected to Docker Engine: v{client.version()['Version']}")
            return client
    except docker.errors.APIError as e:
        logger.error(f"Docker API error during connect: {e}")


@asynccontextmanager
async def connect_to_aiodocker():
    client = aiodocker.Docker()
    try:

        if (await client._query("_ping")).status == 200:
            resp = await client._query("version")
            version = (await resp.json())["Version"]
            logger.debug(f"Connected to Docker Engine: v{version}")
            yield client
    finally:
        await client.close()
        logger.info("Docker connection closed.")


@contextmanager
def docker_context(path, dirs=None):
    """
    Tars and compresses the given docker context in memory. Useful for sending contexts to `docker build` commands.
    :param path: str or pathlib.Path object representing the path of the context
    :param dirs: white list of directories under path to grab
    :return: an in memory tar of the context
    """
    if not isinstance(path, Path):
        try:
            path = Path(path)
        except (ValueError, NotImplementedError):
            logger.exception(f"Error accessing path: \"{path}\"")
            return

    fileobj = BytesIO()
    tar = tarfile.open(fileobj=fileobj, mode="w")

    # If a list of subdirectories is listed, only grab them
    if dirs is not None:
        for d in dirs:
            tar.add(path / d, arcname=d)
    else:
        tar.add(path, arcname='')
    tar.close()
    try:
        fileobj.seek(0)  # must go back to start of file after tarfile writes to it
        yield fileobj
    finally:
        fileobj.close()


async def stream_docker_log(log_stream):
    async for line in log_stream:
        if "stream" in line and line["stream"].strip():
            logger.debug(line["stream"].strip())
        elif "status" in line:
            logger.debug(line["status"].strip())
        elif "error" in line:
            logger.error(line["error"].strip())
            raise DockerBuildError
