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
    # Common options
    API_GATEWAY_URI = os.getenv("API_GATEWAY_URI", "http://api_gateway:8080")
    REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")
    ENCRYPTION_KEY_PATH = os.getenv("ENCRYPTION_KEY_PATH", "/run/secrets/encryption_key")
    # Worker options
    WORKER_TIMEOUT = os.getenv("WORKER_TIMEOUT", "30")
    WALKOFF_USERNAME = os.getenv("WALKOFF_USERNAME", '')
    WALKOFF_PASSWORD = os.getenv("WALKOFF_PASSWORD", '')

    # Umpire options
    APPS_PATH = os.getenv("APPS_PATH", "./apps")
    APP_REFRESH = os.getenv("APP_REFRESH", "60")
    SWARM_NETWORK = os.getenv("SWARM_NETWORK", "walkoff_default")
    APP_PREFIX = os.getenv("APP_PREFIX", "walkoff_app")
    STACK_PREFIX = os.getenv("STACK_PREFIX", "walkoff")
    DOCKER_REGISTRY = os.getenv("DOCKER_REGISTRY", "127.0.0.1:5000")
    UMPIRE_HEARTBEAT = os.getenv("UMPIRE_HEARTBEAT", "1")

    # Redis options
    REDIS_EXECUTING_WORKFLOWS = "executing-workflows"
    REDIS_PENDING_WORKFLOWS = "pending-workflows"
    REDIS_ABORTING_WORKFLOWS = "aborting-workflows"
    REDIS_ACTIONS_IN_PROCESS = "actions-in-process"
    REDIS_WORKFLOW_QUEUE = "workflow-queue"
    REDIS_WORKFLOWS_IN_PROCESS = "workflows-in-process"
    REDIS_WORKFLOW_GROUP = "workflow-group"
    REDIS_ACTION_RESULTS_GROUP = "action-results-group"
    REDIS_WORKFLOW_TRIGGERS_GROUP = "workflow-triggers-group"
    REDIS_WORKFLOW_CONTROL = "workflow-control"
    REDIS_WORKFLOW_CONTROL_GROUP = "workflow-control-group"

    # API Gateway options
    DB_TYPE = os.getenv("DB_TYPE", "postgres")
    DB_HOST = os.getenv("DB_HOST", "postgres")
    SERVER_DB_NAME = os.getenv("SERVER_DB", "walkoff")
    EXECUTION_DB_NAME = os.getenv("EXECUTION_DB", "execution")
    DB_USERNAME = os.getenv("DB_USERNAME", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    API_PATH = Path("api_gateway") / "api"
    CLIENT_PATH = Path("api_gateway") / "client"
    SWAGGER_URL = "/api/docs"

    # Overrides the environment variables for docker-compose and docker commands on the docker machine at 'DOCKER_HOST'
    # See: https://docs.docker.com/compose/reference/envvars/ for more information.
    # DOCKER_HOST = os.getenv("DOCKER_HOST", "tcp://ip_of_docker_swarm_manager:2376")
    # DOCKER_HOST = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
    # DOCKER_TLS_VERIFY = os.getenv("DOCKER_TLS_VERIFY", "1")
    # DOCKER_CERT_PATH = os.getenv("DOCKER_CERT_PATH", "/Path/to/certs/for/remote/docker/daemon")

    def get_int(self, key, default):
        return sint(getattr(self, key), default)

    def get_float(self, key, default):
        return sfloat(getattr(self, key), default)


config = Config()
