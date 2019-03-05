import logging
import os
from contextlib import asynccontextmanager

import aioredis
import yaml
import docker
import docker.tls
import docker.errors
import docker.types
from docker.utils.utils import parse_bytes
from docker.types.services import ServiceMode, Resources, EndpointSpec, RestartPolicy

from compose import timeparse
from compose.config.environment import Environment

from common.config import config

logger = logging.getLogger("WALKOFF")


def sint(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def sfloat(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


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
async def connect_to_redis_pool(redis_uri) -> aioredis.Redis:
    # Redis client bound to pool of connections (auto-reconnecting).
    redis = await aioredis.create_redis_pool(redis_uri)
    try:
        yield redis
    finally:
        # gracefully close pool
        redis.close()
        await redis.wait_closed()
        logger.info("Redis connection pool closed.")


def validate_app_api(api_file):
    #  TODO: Actually validate the api
    with open(api_file, 'r') as fp:
        try:
            return yaml.load(fp)
        except yaml.YAMLError as exc:
            logger.exception(exc)


class ServiceKwargs:
    def __init__(self, args=None, constraints=None, preferences=None, platforms=None, container_labels=None,
                 endpoint_spec=None, env=None, hostname=None, isolation=None, labels=None, log_driver=None,
                 log_driver_options=None, mode=None, mounts=None, name=None, networks=None, resources=None,
                 restart_policy=None, secrets=None, stop_grace_period=None, update_config=None, user=None,
                 workdir=None, tty=None, groups=None, open_stdin=None, read_only=None, stop_signal=None,
                 healthcheck=None, hosts=None, dns_config=None, configs=None, privileges=None):
        self.args = args
        self.constraints = constraints
        self.preferences = preferences
        self.platforms = platforms
        self.container_labels = container_labels
        self.endpoint_spec = endpoint_spec
        self.env = env
        self.hostname = hostname
        self.isolation = isolation
        self.labels = labels
        self.log_driver = log_driver
        self.log_driver_options = log_driver_options
        self.mode = mode
        self.mounts = mounts
        self.name = name
        self.networks = networks
        self.resources = resources
        self.restart_policy = restart_policy
        self.secrets = secrets
        self.stop_grace_period = stop_grace_period
        self.update_config = update_config
        self.user = user
        self.workdir = workdir
        self.tty = tty
        self.groups = groups
        self.open_stdin = open_stdin
        self.read_only = read_only
        self.stop_signal = stop_signal
        self.healthcheck = healthcheck
        self.hosts = hosts
        self.dns_config = dns_config
        self.configs = configs
        self.privileges = privileges

    def update(self, other, **kwargs):
        try:
            iter(other)
            keys_method = getattr(other, "items")
            if callable(keys_method):  # it's a dictionary
                for key, value in other.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
            else:  # it's a different iterable
                for key, value in other:
                    if hasattr(self, key):
                        setattr(self, key, value)
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        except TypeError:
            return

    def as_dict(self):
        return self.__dict__

    def configure(self, service, secrets=None):
        """ Parameters:
                image (str) – The image name to use for the containers.
                command (list of str or str) – Command to run.
                args (list of str) – Arguments to the command.
                constraints (list of str) – Placement constraints.
                preferences (list of tuple) – Placement preferences.
                platforms (list of tuple) – A list of platform constraints expressed as (arch, os) tuples.
                container_labels (dict) – Labels to apply to the container.
                endpoint_spec (EndpointSpec) – Properties that can be configured to access and load balance a service. Default: None.
                env (list of str) – Environment variables, in the form KEY=val.
                hostname (string) – Hostname to set on the container.
                isolation (string) – Isolation technology used by the service’s containers. Only used for Windows containers.
                labels (dict) – Labels to apply to the service.
                log_driver (str) – Log driver to use for containers.
                log_driver_options (dict) – Log driver options.
                mode (ServiceMode) – Scheduling mode for the service. Default:None
                mounts (list of str) – Mounts for the containers, in the form source:target:options, where options is either ro or rw.
                name (str) – Name to give to the service.
                networks (list of str) – List of network names or IDs to attach the service to. Default: None.
                resources (Resources) – Resource limits and reservations.
                restart_policy (RestartPolicy) – Restart policy for containers.
                secrets (list of docker.types.SecretReference) – List of secrets accessible to containers for this service.
                stop_grace_period (int) – Amount of time to wait for containers to terminate before forcefully killing them.
                update_config (UpdateConfig) – Specification for the update strategy of the service. Default: None
                rollback_config (RollbackConfig) – Specification for the rollback strategy of the service. Default: None
                user (str) – User to run commands as.
                workdir (str) – Working directory for commands to run.
                tty (boolean) – Whether a pseudo-TTY should be allocated.
                groups (list) – A list of additional groups that the container process will run as.
                open_stdin (boolean) – Open stdin
                read_only (boolean) – Mount the container’s root filesystem as read only.
                stop_signal (string) – Set signal to stop the service’s containers
                healthcheck (Healthcheck) – Healthcheck configuration for this service.
                hosts (dict) – A set of host to IP mappings to add to the container’s hosts file.
                dns_config (DNSConfig) – Specification for DNS related configurations in resolver configuration file.
                configs (list) – List of ConfigReference that will be exposed to the service.
                privileges (Privileges) – Security options for the service’s containers.
        """

        options = service.options
        deploy_opts = options.get("deploy", {})
        prefs = deploy_opts.get("placement", {}).get("preferences", {})

        # Map compose options to service options
        self.constraints = deploy_opts.get("placement", {}).get("constraints")
        self.preferences = [kv for pref in prefs for kv in pref.items()]
        self.container_labels = options.get("labels")

        self.endpoint_spec = EndpointSpec(deploy_opts.get("endpoint_mode"),
                                          {p.published: p.target for p in options.get("ports", [])})

        self.env = [f"{k}={v}" for k, v in options.get("environment").items()]
        self.hostname = options.get("hostname")
        self.isolation = options.get("isolation")
        self.labels = {k: v for k, v in (kv.split('=') for kv in deploy_opts.get("labels", []))}
        self.log_driver = options.get("logging", {}).get("driver")
        self.log_driver_options = options.get("logging", {}).get("options")
        self.mode = ServiceMode(deploy_opts.get("mode", "replicated"), deploy_opts.get("replicas", 1))
        self.mounts = None  # I'm not sure we should allow mounting volumes to apps until I see a use case
        self.name = service.name
        self.networks = None  # Similar to mounts. I don't see the use case but see the issues

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
            delay = timeparse.timeparse(restart_opts.get("delay", "0s"))
            window = timeparse.timeparse(restart_opts.get("restart_opts", "0s"))
            self.restart_policy = RestartPolicy(condition=restart_opts.get("condition", ),
                                                delay=delay,
                                                max_attempts=sint(restart_opts.get("max_attempts", 0)),
                                                window=window)

        # self.secrets = [SecretReference(secret_id=s["secret"].uid, secret_name=s["secret"].name, filename=s.get("file", s["secret"].name), uid=s["secret"].uid, gid=s["secret"].gid, mode=s["secret"].mode) for s in service.secrets]
        # self.secrets = self.load_secrets(service)

        return {key: value for key, value in self.as_dict().items() if value is not None}
