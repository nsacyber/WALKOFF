import logging
from pathlib import Path
import os


logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("WALKOFF")
CONFIG_PATH = (Path(__file__).parent / "config.ini").resolve()


def sint(value, default):
    if not isinstance(default, int):
        raise TypeError("Default value must be of integer type")
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sfloat(value, default):
    if not isinstance(default, int):
        raise TypeError("Default value must be of float type")
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class Config:
    # Worker options
    WORKER_TIMEOUT = os.environ.get("WORKER_TIMEOUT", "30")
    API_GATEWAY_URI = os.environ.get("API_GATEWAY_URI", "http://api_gateway:8080")
    WALKOFF_USERNAME = os.environ.get("WALKOFF_USERNAME", '')
    WALKOFF_PASSWORD = os.environ.get("WALKOFF_PASSWORD", '')

    # Umpire options
    APPS_PATH = os.environ.get("APPS_PATH", "./apps")
    APP_REFRESH = os.environ.get("APP_REFRESH", "60")
    SWARM_NETWORK = os.environ.get("SWARM_NETWORK", "walkoff_default")
    APP_PREFIX = os.environ.get("APP_PREFIX", "walkoff_app")
    STACK_PREFIX = os.environ.get("STACK_PREFIX", "walkoff")
    DOCKER_REGISTRY = os.environ.get("DOCKER_REGISTRY", "localhost:5000")
    UMPIRE_HEARTBEAT = os.environ.get("UMPIRE_HEARTBEAT", "1")

    # Redis options
    REDIS_URI = os.environ.get("REDIS_URI", "redis://redis:6379")
    REDIS_ACTION_RESULTS = os.environ.get("REDIS_ACTION_RESULTS", "action-results")
    REDIS_ACTIONS_IN_PROCESS = os.environ.get("REDIS_ACTIONS_IN_PROCESS", "actions-in-process")
    REDIS_WORKFLOW_QUEUE = os.environ.get("REDIS_WORKFLOW_Q", "workflow-queue")
    REDIS_WORKFLOWS_IN_PROCESS = os.environ.get("REDIS_WORKFLOWS_IN_PROCESS", "workflows-in-process")
    REDIS_WORKFLOW_GROUP = os.environ.get("REDIS_WORKFLOW_GROUP", "workflow-group")
    REDIS_ACTION_RESULTS_GROUP = os.environ.get("REDIS_ACTION_RESULTS_GROUP", "action-results-group")
    # Overrides the environment variables for docker-compose and docker commands on the docker machine at 'DOCKER_HOST'
    # See: https://docs.docker.com/compose/reference/envvars/ for more information.
    # DOCKER_HOST = os.environ.get("DOCKER_HOST", "tcp://ip_of_docker_swarm_manager:2376")
    # DOCKER_HOST = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
    # DOCKER_TLS_VERIFY = os.environ.get("DOCKER_TLS_VERIFY", "1")
    # DOCKER_CERT_PATH = os.environ.get("DOCKER_CERT_PATH", "/Path/to/certs/for/remote/docker/daemon")

    def get_int(self, key, default):
        return sint(getattr(self, key), default)

    def get_float(self, key, default):
        return sfloat(getattr(self, key), default)


config = Config()
