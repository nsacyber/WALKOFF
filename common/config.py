import logging
from pathlib import Path
import os
import socket

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
    CONTAINER_ID = os.getenv("HOSTNAME", socket.gethostname())

    # Prefixes
    STACK_PREFIX = "walkoff"
    CORE_PREFIX = f"{STACK_PREFIX}_core"
    RESOURCE_PREFIX = f"{STACK_PREFIX}_resource"
    APP_PREFIX = f"{STACK_PREFIX}_app"

    # Core services
    API_SERVICE = f"{CORE_PREFIX}_api"
    UMPIRE_SERVICE = f"{CORE_PREFIX}_umpire"
    WORKER_SERVICE = f"{CORE_PREFIX}_worker"
    SOCKETIO_SERVICE = f"{CORE_PREFIX}_socketio"

    # Resource services
    REDIS_SERVICE = f"{RESOURCE_PREFIX}_redis"
    POSTGRES_SERVICE = f"{RESOURCE_PREFIX}_postgres"
    NGINX_SERVICE = f"{RESOURCE_PREFIX}_nginx"
    PORTAINER_SERVICE = f"{RESOURCE_PREFIX}_portainer"
    REGISTRY_SERVICE = f"{RESOURCE_PREFIX}_registry"
    MINIO_SERVICE = f"{RESOURCE_PREFIX}_minio"
    MONGO_SERVICE = f"{RESOURCE_PREFIX}_mongo"

    # Volume names
    REGISTRY_VOLUME = f"{REGISTRY_SERVICE}_volume"
    MINIO_VOLUME = f"{MINIO_SERVICE}_volume"
    PORTAINER_VOLUME = f"{PORTAINER_SERVICE}_volume"
    MONGO_VOLUME = f"{MONGO_SERVICE}_volume"

    # Secret names
    ENCRYPTION_KEY = f"{STACK_PREFIX}_encryption_key"
    INTERNAL_KEY = f"{STACK_PREFIX}_internal_key"
    POSTGRES_KEY = f"{STACK_PREFIX}_postgres_key"
    MINIO_ACCESS_KEY = f"{STACK_PREFIX}_minio_access_key"
    MINIO_SECRET_KEY = f"{STACK_PREFIX}_minio_secret_key"
    REDIS_KEY = f"{STACK_PREFIX}_redis_key"
    MONGO_KEY = f"{STACK_PREFIX}_mongo_key"

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
    REDIS_RESULTS_QUEUE = "results-queue"

    # File paths
    # API_PATH = Path("api") / "api"
    CLIENT_PATH = Path("api") / "client"
    TEMPLATE_PATH = Path("api") / "server" / "templates"
    SECRET_BASE_PATH = Path("/") / "run" / "secrets"

    SOCKETIO_PATH = "/walkoff/sockets/socket.io"
    SIO_NS_CONSOLE = "/console"
    SIO_NS_NODE = "/nodeStatus"
    SIO_NS_WORKFLOW = "/workflowStatus"
    SIO_NS_BUILD = "/buildStatus"
    SIO_EVENT_LOG = "log"

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
    API_URI = os.getenv("API_URI", f"http://{Static.API_SERVICE}:8080")
    REDIS_URI = os.getenv("REDIS_URI", f"redis://{Static.REDIS_SERVICE}:6379")
    MINIO = os.getenv("MINIO", f"{Static.MINIO_SERVICE}:9000")
    SOCKETIO_URI = os.getenv("SOCKETIO_URI", f"http://{Static.SOCKETIO_SERVICE}:3000")

    # Key locations
    ENCRYPTION_KEY_PATH = os.getenv("ENCRYPTION_KEY_PATH", Static.SECRET_BASE_PATH / Static.ENCRYPTION_KEY)
    INTERNAL_KEY_PATH = os.getenv("INTERNAL_KEY_PATH", Static.SECRET_BASE_PATH / Static.INTERNAL_KEY)
    POSTGRES_KEY_PATH = os.getenv("POSTGRES_KEY_PATH", Static.SECRET_BASE_PATH / Static.POSTGRES_KEY)
    REDIS_KEY_PATH = os.getenv("REDIS_KEY_PATH", Static.SECRET_BASE_PATH / Static.REDIS_KEY)
    MINIO_ACCESS_KEY_PATH = os.getenv("MINIO_SECRET_KEY_PATH", Static.SECRET_BASE_PATH / Static.MINIO_ACCESS_KEY)
    MINIO_SECRET_KEY_PATH = os.getenv("MINIO_SECRET_KEY_PATH", Static.SECRET_BASE_PATH / Static.MINIO_SECRET_KEY)
    MONGO_KEY_PATH = os.getenv("MONGO_KEY_PATH", Static.SECRET_BASE_PATH / Static.MONGO_KEY)

    # Worker options
    MAX_WORKER_REPLICAS = os.getenv("MAX_WORKER_REPLICAS", "10")
    WORKER_TIMEOUT = os.getenv("WORKER_TIMEOUT", "30")
    WALKOFF_USERNAME = os.getenv("WALKOFF_USERNAME", '')

    # Umpire options
    APPS_PATH = os.getenv("APPS_PATH", "./apps")
    APP_REFRESH = os.getenv("APP_REFRESH", "60")
    SWARM_NETWORK = os.getenv("SWARM_NETWORK", "walkoff_network")
    DOCKER_REGISTRY = os.getenv("DOCKER_REGISTRY", "127.0.0.1:5000")
    UMPIRE_HEARTBEAT = os.getenv("UMPIRE_HEARTBEAT", "1")

    # API Gateway options
    DB_TYPE = os.getenv("DB_TYPE", "postgres")
    DB_HOST = os.getenv("DB_HOST", Static.POSTGRES_SERVICE)
    MONGO_HOST = os.getenv("MONGO_HOST", Static.MONGO_SERVICE)
    MONGO_PORT = os.getenv("MONGO_PORT", "27016")
    SERVER_DB_NAME = os.getenv("SERVER_DB", "walkoff")
    EXECUTION_DB_NAME = os.getenv("EXECUTION_DB", "execution")
    DB_USERNAME = os.getenv("DB_USERNAME", "walkoff")

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

    def get_int(self, key, default=None):
        return sint(getattr(self, key), default)

    def get_float(self, key, default=None):
        return sfloat(getattr(self, key), default)

    def load_config(self):
        try:
            with open(CONFIG_PATH) as f:
                y = yaml.safe_load(f)

            for key, value in y.items():
                if hasattr(self, key.upper()) and not os.getenv(key.upper()):
                    setattr(self, key.upper(), value)
        except IOError:
            logger.warning(f"No config file found at {CONFIG_PATH}, using defaults.\n"
                           f"Set the CONFIG_PATH environment variable to point to a config file to override.")

    def dump_config(self, file):
        with open(file, 'w') as f:
            yaml.safe_dump(vars(self), f)

    @staticmethod
    def get_from_file(file_path, mode='r'):
        with open(file_path, mode) as f:
            s = f.read().strip()

        return s


config = Config()
config.load_config()

static = Static()
