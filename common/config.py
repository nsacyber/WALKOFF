import logging
import configparser
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("WALKOFF")
CONFIG_PATH = (Path(__file__).parent / "../data/config.ini").resolve()


def load_config():
    try:
        # Load the user configurable parameters
        config = configparser.ConfigParser()
        config.optionxform = str  # override optionxform to preserve case of config keys
        config.read(CONFIG_PATH)

        # Append dev config options or overwrite config options the user shouldn't have set
        redis_keys = {"action_results_ch": "action-results", "actions_in_process": "actions-in-process",
                      "apigateway2umpire_ch": "api-gateway2umpire", "umpire2apigateway_ch": "umpire2api-gateway",
                      "globals_key": "globals", "api_key": "app-apis", "workflow_q": "workflow-queue",
                      "workflows_in_process": "workflows-in-process"}

        # Add redis dev config options to the config
        for key, val in redis_keys.items():
            config.set("REDIS", key, val)

        return config

    except KeyError as e:
        logger.exception(f"Config section {e.args[0]} not found.")
        sys.exit(1)  # Invalid config is grounds for immediate app termination


if __name__ == "__main__":
    config = load_config()
    if config:
        print([key for key in config.keys()])
