import logging
from pathlib import Path
import os

import yaml

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("WALKOFF")
CONFIG_PATH = os.getenv("CONFIG_PATH", "/common_env.yml")


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


class Static:
    """Common location for static values"""

    # Common statics
    CONTAINER_ID = os.getenv("HOSTNAME")

    # Service names
    CORE_PREFIX = "walkoff_core"
    RESOURCE_PREFIX = "walkoff_resource"
    APP_PREFIX = "walkoff_app"

    API_GATEWAY_SERVICE = f"{CORE_PREFIX}_api_gateway"
    UMPIRE_SERVICE = f"{CORE_PREFIX}_umpire"
    WORKER_SERVICE = f"{CORE_PREFIX}_worker"

    REDIS_SERVICE = f"{RESOURCE_PREFIX}_redis"
    POSTGRES_SERVICE = f"{RESOURCE_PREFIX}_postgres"
    NGINX_SERVICE = f"{RESOURCE_PREFIX}_nginx"
    PORTAINER_SERVICE = f"{RESOURCE_PREFIX}_portainer"
    REGISTRY_SERVICE = f"{RESOURCE_PREFIX}_registry"
    MINIO_SERVICE = f"{RESOURCE_PREFIX}_minio"

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

    # API Gateway paths
    API_PATH = Path("api_gateway") / "api"
    CLIENT_PATH = Path("api_gateway") / "client"
    SWAGGER_URL = "/walkoff/api/docs"

    def set_local_hostname(self, hostname):
        if not self.CONTAINER_ID:
            self.CONTAINER_ID = hostname


class Config:
    """Common location for configurable values.
    Precedence:
    1. Environment Variables
    2. Config File
    3. Defaults defined here
    """

    # Common options
    API_GATEWAY_URI = os.getenv("API_GATEWAY_URI", f"http://{Static.API_GATEWAY_SERVICE}:8080")
    REDIS_URI = os.getenv("REDIS_URI", f"redis://{Static.REDIS_SERVICE}:6379")
    ENCRYPTION_KEY_PATH = os.getenv("ENCRYPTION_KEY_PATH", "/run/secrets/walkoff_encryption_key")
    MINIO = os.getenv("MINIO", f"{Static.MINIO_SERVICE}:9000")

    # Worker options
    MAX_WORKER_REPLICAS = os.getenv("MAX_WORKER_REPLICAS", "10")
    WORKER_TIMEOUT = os.getenv("WORKER_TIMEOUT", "30")
    WALKOFF_USERNAME = os.getenv("WALKOFF_USERNAME", '')
    WALKOFF_PASSWORD = os.getenv("WALKOFF_PASSWORD", '')

    # Umpire options
    APPS_PATH = os.getenv("APPS_PATH", "./apps")
    APP_REFRESH = os.getenv("APP_REFRESH", "60")
    DOCKER_REGISTRY = os.getenv("DOCKER_REGISTRY", "127.0.0.1:5000")
    UMPIRE_HEARTBEAT = os.getenv("UMPIRE_HEARTBEAT", "1")

    # API Gateway options
    DB_TYPE = os.getenv("DB_TYPE", "postgres")
    DB_HOST = os.getenv("DB_HOST", Static.POSTGRES_SERVICE)
    SERVER_DB_NAME = os.getenv("SERVER_DB", "walkoff")
    EXECUTION_DB_NAME = os.getenv("EXECUTION_DB", "execution")
    DB_USERNAME = os.getenv("DB_USERNAME", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    # Bootloader options
    BASE_COMPOSE = os.getenv("BASE_COMPOSE", "./bootloader/base-compose.yml")
    WALKOFF_COMPOSE = os.getenv("WALKOFF_COMPOSE", "./bootloader/walkoff-compose.yml")
    TMP_COMPOSE = os.getenv("TMP_COMPOSE", "./tmp-compose.yml")

    # App options
    MAX_APP_REPLICAS = os.getenv("MAX_APP_REPLICAS", "10")
    APP_TIMEOUT = os.getenv("APP_TIMEOUT", "30")  # ??

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

    def load_config(self):
        with open(CONFIG_PATH) as f:
            y = yaml.safe_load(f)

        for key, value in y.items():
            if hasattr(self, key.upper()) and not os.getenv(key.upper()):
                setattr(self, key.upper(), value)


config = Config()
config.load_config()

static = Static()
